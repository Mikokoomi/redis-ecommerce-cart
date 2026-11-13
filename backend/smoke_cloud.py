"""Kiểm thử Cloud chủ động: python -m backend.smoke_cloud."""
import sys
from uuid import uuid4
import httpx
from redis.exceptions import RedisError
from .redis_client import create_redis_client
from .seed import CATEGORIES


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    db = create_redis_client()
    if db is None:
        print("CONFIG_MISSING: kiểm tra .env và các biến bắt buộc.")
        return 1
    key = "cart:codex_smoke_" + uuid4().hex
    try:
        assert db.ping()
        print("Redis PING: OK")
        print("products:", db.scard("products:all"))
        print("categories:", {c: db.scard("products:category:" + c) for c in CATEGORIES})
        print("sample_carts:", {u: {"type": db.type("cart:"+u), "ttl": db.ttl("cart:"+u)} for u in ["demo","user001","user002","user003"]})
        assert db.type("products:all") == "set"
        assert all(db.type("products:category:"+c) == "set" for c in CATEGORIES)
        ids = db.smembers("products:all")
        assert len(ids) == 20
        assert all(db.type("product:"+pid) == "hash" and db.ttl("product:"+pid) == -1 for pid in ids)
        with httpx.Client(base_url="http://127.0.0.1:8017", timeout=30) as c:
            for path in ["/","/health","/health/redis","/api/products","/api/products/SP001","/api/products?category=dien-thoai","/api/cart/demo","/css/style.css","/js/app.js"]:
                r = c.get(path)
                assert r.status_code == 200, (path,r.status_code)
                print("HTTP 200", path)
            assert len(c.get("/api/products").json()) == 20
            assert len(c.get("/api/products?category=dien-thoai").json()) == 4
            p = "/api/cart/" + key.removeprefix("cart:")
            assert not db.exists(key)
            assert c.get(p).json()["items"] == []
            def check(r, expected):
                assert r.status_code == 200
                data = r.json()
                assert db.hgetall(key) == {pid:str(q) for pid,q in expected.items()}
                assert data["total_quantity"] == sum(expected.values())
                total = sum(int(db.hget("product:"+pid,"price_vnd"))*q for pid,q in expected.items())
                assert data["total_vnd"] == total
                return data
            check(c.post(p+"/items",json={"product_id":"SP001","quantity":2}), {"SP001":2})
            check(c.post(p+"/items",json={"product_id":"SP001","quantity":3}), {"SP001":5})
            check(c.post(p+"/items",json={"product_id":"SP002","quantity":1}), {"SP001":5,"SP002":1})
            check(c.patch(p+"/items/SP001",json={"quantity":4}), {"SP001":4,"SP002":1})
            check(c.delete(p+"/items/SP002"), {"SP001":4})
            check(c.get(p), {"SP001":4})
            assert db.type(key) == "hash"
            assert 86300 < db.ttl(key) <= 86400
            check(c.delete(p), {})
            assert not db.exists(key)
            print("Cloud CRUD, totals, reload, Hash, TTL, cleanup: OK")
        return 0
    except RedisError as exc:
        print("Redis error type:", type(exc).__name__)
        return 1
    finally:
        # Chỉ xóa chính xác giỏ mang UUID của lần chạy này.
        try:
            db.delete(key)
        except RedisError:
            print("Không thể xác nhận cleanup; giỏ thử có TTL tối đa 24 giờ.")
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
