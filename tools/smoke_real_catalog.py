"""Smoke test Cloud trên key dùng một lần; không checkout 20 sản phẩm catalogue."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import random
import sys
from uuid import uuid4

import httpx
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.catalog_import import backup_catalog, load_catalog, CATEGORIES
from backend.redis_client import create_redis_client

def main():
    db=create_redis_client()
    if db is None:raise SystemExit("Missing Redis config")
    token=uuid4().hex
    user="codex_smoke_real_"+token
    request_key="catalog_"+token
    cart_key="cart:"+user
    idem="checkout:request:"+hashlib.sha256(json.dumps([user,request_key]).encode()).hexdigest()
    product_key=None
    created=False
    order_id=None
    try:
        assert db.ping()
        print("PRE_TEST_BACKUP",backup_catalog(db))
        catalogue_stock={p["id"]:db.hget("product:"+p["id"],"stock") for p in load_catalog()["products"]}
        with httpx.Client(base_url="http://127.0.0.1:8017",timeout=30) as c:
            data=c.get("/api/products")
            assert data.status_code==200 and len(data.json())==20
            assert len(list(db.scan_iter(match="product:*",count=100)))==20
            for category in CATEGORIES.values():
                r=c.get("/api/products",params={"category":category})
                assert r.status_code==200 and len(r.json())==4
            for p in data.json():
                detail=c.get("/api/products/"+p["product_id"])
                assert detail.status_code==200 and isinstance(detail.json()["specs"],dict) and detail.json()["specs"]
                r=c.get(p["image"])
                assert r.status_code==200 and r.headers["content-type"].startswith("image/")
                with Image.open(BytesIO(r.content)) as img:
                    img.load()
                    assert img.width>=300 and img.format=="WEBP"
            print("API_PRODUCTS_20_DETAILS_20_CATEGORIES_5_IMAGES_20_OK")
            source=db.hgetall("product:SP001")
            # Chỉ dùng ID 3 chữ số ngoài catalogue; tạo nếu chưa tồn tại.
            for number in random.sample(range(800,1000),200):
                pid=f"SP{number:03}"
                product_key="product:"+pid
                with db.pipeline() as pipe:
                    pipe.watch(product_key,cart_key,idem)
                    if pipe.exists(product_key) or pipe.exists(cart_key) or pipe.exists(idem):
                        continue
                    pipe.multi()
                    pipe.hset(product_key,mapping={**source,"product_id":pid,"name":"Smoke test "+token,"stock":5,"smoke_owner":token})
                    pipe.execute()
                    created=True
                    break
            assert created
            path="/api/cart/"+user
            for quantity in [1,1]:
                r=c.post(path+"/items",json={"product_id":pid,"quantity":quantity})
                assert r.status_code==200
            assert db.hget(product_key,"stock")=="5"
            assert c.get(path).json()["total_quantity"]==2
            r=c.patch(path+"/items/"+pid,json={"quantity":3})
            assert r.status_code==200 and db.hget(product_key,"stock")=="5"
            assert c.get(path).json()["total_quantity"]==3
            request={"confirmed":True,"idempotency_key":request_key}
            r=c.post(path+"/checkout",json=request)
            assert r.status_code==200
            order=r.json()
            order_id=order["order_id"]
            assert order["total_vnd"]==3*int(source["price_vnd"])
            assert db.hget(product_key,"stock")=="2"
            assert not db.exists(cart_key)
            assert c.post(path+"/checkout",json=request).json()==order
            assert db.hget(product_key,"stock")=="2"
            assert c.get(path+"/orders/"+order_id).json()==order
            print("ISOLATED_CLOUD_CART_STOCK_5_UNCHANGED_CHECKOUT_5_TO_2_IDEMPOTENCY_OK")
            assert all(db.hget("product:"+pid,"stock")==stock for pid,stock in catalogue_stock.items())
            print("ALL_20_CATALOGUE_STOCK_UNCHANGED")
    finally:
        if created:
            # Chỉ dọn đúng những key đã tạo và chứng minh ownership.
            if db.hget(product_key,"smoke_owner")==token:
                saved=db.get(idem)
                candidate=saved or order_id
                cleanup=[product_key,cart_key]
                if candidate and db.hget("order:"+candidate,"user_id")==user:
                    cleanup.extend(["order:"+candidate,"order:"+candidate+":items",idem])
                db.delete(*cleanup)
                assert all(not db.exists(k) for k in cleanup)
                print("EXACT_OWNED_TEST_KEYS_CLEANED",len(cleanup))
            else:
                raise RuntimeError("Ownership changed; cleanup stopped.")
        db.close()

if __name__=="__main__":
    main()

