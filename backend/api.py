from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from redis.exceptions import WatchError
from .redis_client import create_redis_client
from .config import CART_TTL_SECONDS
from .checkout import checkout, read_order
from typing import Literal
import json

router = APIRouter(prefix="/api")

def database():
    client = create_redis_client()
    if client is None:
        raise HTTPException(503, "Redis chưa được cấu hình.")
    try:
        yield client
    finally:
        client.close()

def product(db, pid):
    data = db.hgetall("product:" + pid)
    if not data:
        raise HTTPException(404, "Sản phẩm không tồn tại.")
    try:
        specs = json.loads(data.get("specs", "{}"))
    except (ValueError, TypeError):
        specs = {}
    return {**data, "specs": specs if isinstance(specs, dict) else {}, "product_id": pid, "price_vnd": int(data["price_vnd"]), "stock": int(data["stock"])}

def cart(db, user_id):
    items = []
    for pid, quantity in sorted(db.hgetall("cart:" + user_id).items()):
        try:
            p = product(db, pid)
        except HTTPException:
            p = {"product_id": pid, "name": "Sản phẩm không còn tồn tại", "price_vnd": 0, "image": "/assets/phu-kien.svg"}
        items.append({**p, "quantity": int(quantity), "subtotal_vnd": p["price_vnd"] * int(quantity)})
    return {"items": items, "total_quantity": sum(i["quantity"] for i in items), "total_vnd": sum(i["subtotal_vnd"] for i in items), "ttl": db.ttl("cart:" + user_id)}

class Quantity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: int = Field(ge=0, le=99, strict=True)

class Item(Quantity):
    product_id: str = Field(pattern=r"^SP[0-9]{3}$")


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    confirmed: Literal[True]


@router.post("/cart/{user_id}/checkout")
def confirm_checkout(user_id: str, request: CheckoutRequest, db=Depends(database)):
    return checkout(db, user_id, request.idempotency_key)


@router.get("/cart/{user_id}/orders/{order_id}")
def order_detail(user_id: str, order_id: str, db=Depends(database)):
    return read_order(db, order_id, user_id)

@router.get("/products")
def products(category: str | None = None, db=Depends(database)):
    key = "products:all" if category is None else "products:category:" + category
    return [product(db, pid) for pid in sorted(db.smembers(key))]

@router.get("/products/{product_id}")
def detail(product_id: str, db=Depends(database)):
    return product(db, product_id)

@router.get("/cart/{user_id}")
def get_cart(user_id: str, db=Depends(database)):
    return cart(db, user_id)

def mutate(db, user_id, pid, quantity, increment=False):
    product(db, pid)
    key = "cart:" + user_id
    for _ in range(8):
        with db.pipeline() as pipe:
            try:
                pipe.watch(key)
                amount = quantity + int(pipe.hget(key, pid) or 0) if increment and quantity else quantity
                if amount > 99:
                    raise HTTPException(422, "Tối đa 99 đơn vị mỗi sản phẩm.")
                pipe.multi()
                if amount:
                    pipe.hset(key, pid, amount)
                else:
                    pipe.hdel(key, pid)
                pipe.expire(key, CART_TTL_SECONDS)
                pipe.execute()
                return cart(db, user_id)
            except WatchError:
                continue
    raise HTTPException(409, "Giỏ hàng đang thay đổi. Vui lòng thử lại.")

@router.post("/cart/{user_id}/items")
def add(user_id: str, item: Item, db=Depends(database)):
    return mutate(db, user_id, item.product_id, item.quantity, True)

@router.patch("/cart/{user_id}/items/{product_id}")
def update(user_id: str, product_id: str, item: Quantity, db=Depends(database)):
    return mutate(db, user_id, product_id, item.quantity)

@router.delete("/cart/{user_id}/items/{product_id}")
def remove(user_id: str, product_id: str, db=Depends(database)):
    key = "cart:" + user_id
    with db.pipeline(transaction=True) as pipe:
        pipe.hdel(key, product_id)
        pipe.expire(key, CART_TTL_SECONDS)
        pipe.execute()
    return cart(db, user_id)

@router.delete("/cart/{user_id}")
def clear(user_id: str, db=Depends(database)):
    db.delete("cart:" + user_id)
    return cart(db, user_id)

