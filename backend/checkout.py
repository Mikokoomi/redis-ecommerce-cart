"""Xác nhận mua mô phỏng bằng giao dịch Redis."""
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from redis.exceptions import WatchError


def read_order(db, order_id, user_id):
    data = db.hgetall("order:" + order_id)
    if not data or data.get("user_id") != user_id:
        raise HTTPException(404, "Không tìm thấy đơn hàng.")
    return {**data, "total_vnd": int(data["total_vnd"]),
            "items": [json.loads(v) for _, v in sorted(db.hgetall("order:" + order_id + ":items").items())]}


def checkout(db, user_id, request_key):
    digest = hashlib.sha256(json.dumps([user_id, request_key]).encode()).hexdigest()
    idem = "checkout:request:" + digest
    cart_key = "cart:" + user_id
    order_id = uuid4().hex
    order_key = "order:" + order_id
    items_key = order_key + ":items"
    for _ in range(8):
        with db.pipeline() as pipe:
            try:
                pipe.watch(idem, cart_key, order_key, items_key)
                previous = pipe.get(idem)
                if previous:
                    pipe.unwatch()
                    return read_order(db, previous, user_id)
                if pipe.exists(order_key) or pipe.exists(items_key):
                    raise HTTPException(409, "Mã đơn bị trùng. Vui lòng thử lại.")
                quantities = pipe.hgetall(cart_key)
                if not quantities:
                    raise HTTPException(400, "Giỏ hàng đang trống.")
                product_keys = ["product:" + pid for pid in quantities]
                pipe.watch(*product_keys)
                items, stocks = [], {}
                for pid, quantity in sorted(quantities.items()):
                    p = pipe.hgetall("product:" + pid)
                    if not p:
                        raise HTTPException(409, f"Sản phẩm {pid} không còn tồn tại.")
                    try:
                        q, stock, price = int(quantity), int(p["stock"]), int(p["price_vnd"])
                        if not 1 <= q <= 99 or stock < 0 or price < 0:
                            raise ValueError
                    except (ValueError, KeyError):
                        raise HTTPException(409, f"Dữ liệu sản phẩm hoặc số lượng {pid} không hợp lệ.")
                    if stock < q:
                        raise HTTPException(409, f"{p.get('name', pid)} ({pid}) không đủ hàng: còn {stock}, cần {q}.")
                    stocks[pid] = stock - q
                    items.append({"product_id": pid, "product_name": p.get("name", pid),
                                  "quantity": q, "unit_price_vnd": price, "subtotal_vnd": price * q})
                order = {"order_id": order_id, "user_id": user_id,
                         "total_vnd": sum(i["subtotal_vnd"] for i in items),
                         "status": "CONFIRMED_DEMO",
                         "created_at": datetime.now(timezone.utc).isoformat()}
                pipe.multi()
                for pid, remaining in stocks.items():
                    pipe.hset("product:" + pid, "stock", remaining)
                pipe.hset(order_key, mapping=order)
                pipe.hset(items_key, mapping={i["product_id"]: json.dumps(i, ensure_ascii=False) for i in items})
                pipe.set(idem, order_id)
                pipe.delete(cart_key)
                pipe.execute()
                return {**order, "items": items}
            except WatchError:
                continue
    raise HTTPException(409, "Dữ liệu vừa thay đổi. Vui lòng gửi lại cùng mã yêu cầu.")

