"""Dữ liệu minh họa, không phải báo giá thương mại."""
import argparse
from redis.exceptions import RedisError
from .redis_client import create_redis_client
from .config import CART_TTL_SECONDS

CATEGORIES = {
    "dien-thoai": ["Điện thoại Nova A15", "Điện thoại Nova S24", "Điện thoại Lumi 12", "Điện thoại Lumi Pro"],
    "laptop": ["Laptop Study 14", "Laptop Work 15", "Laptop Air 13", "Laptop Creator 16"],
    "tai-nghe": ["Tai nghe không dây Mini", "Tai nghe chụp tai Studio", "Tai nghe thể thao Fit", "Tai nghe có dây Basic"],
    "dong-ho": ["Đồng hồ Active", "Đồng hồ Sport", "Đồng hồ Classic", "Đồng hồ Mini"],
    "phu-kien": ["Sạc nhanh USB-C", "Cáp USB-C 1 mét", "Pin dự phòng 10000mAh", "Đế kê laptop"],
}
PRICES = [[4500000,12000000,6500000,15000000],[12500000,16000000,19000000,24000000],[450000,1200000,650000,180000],[1500000,2200000,2800000,900000],[290000,90000,450000,350000]]

def seed(db, carts=False, update=False):
    counts = {"created": 0, "skipped": 0, "updated": 0}
    for group, (category, names) in enumerate(CATEGORIES.items()):
        for index, name in enumerate(names):
            pid = f"SP{group * 4 + index + 1:03}"
            key = "product:" + pid
            data = {"product_id": pid, "name": name, "description": f"{name}, thiết kế tiện dụng cho học tập và cuộc sống. Dữ liệu mẫu đồ án.", "price_vnd": PRICES[group][index], "category": category, "image": f"/assets/{category}.svg", "stock": 20 + index}
            # WATCH bảo vệ dữ liệu nếu seed đồng thời.
            from redis.exceptions import WatchError
            while True:
                with db.pipeline() as pipe:
                    try:
                        pipe.watch(key)
                        exists = pipe.exists(key)
                        current_category = pipe.hget(key, "category") if exists else None
                        pipe.multi()
                        if not exists or update:
                            pipe.hset(key, mapping=data)
                            if current_category and current_category != category:
                                pipe.srem("products:category:" + current_category, pid)
                        pipe.sadd("products:all", pid)
                        pipe.sadd("products:category:" + (category if update or not exists else current_category or category), pid)
                        pipe.execute()
                        counts["updated" if exists and update else "skipped" if exists else "created"] += 1
                        break
                    except WatchError:
                        continue
    cart_counts = {"created": 0, "skipped": 0}
    if carts:
        for index, user in enumerate(["demo", "user001", "user002", "user003"]):
            key = "cart:" + user
            while True:
                with db.pipeline() as pipe:
                    try:
                        pipe.watch(key)
                        if pipe.exists(key):
                            cart_counts["skipped"] += 1
                            break
                        pipe.multi()
                        pipe.hset(key, mapping={f"SP{index+1:03}": 2, f"SP{index+5:03}": 1})
                        pipe.expire(key, CART_TTL_SECONDS)
                        pipe.execute()
                        cart_counts["created"] += 1
                        break
                    except WatchError:
                        continue
    return {"products": counts, "carts": cart_counts}

def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--carts", action="store_true")
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    if args.update and input("Cập nhật 20 sản phẩm mẫu? Nhập CAP NHAT: ") != "CAP NHAT":
        print("Đã hủy.")
        return
    db = create_redis_client()
    if db is None:
        print("Chưa cấu hình Redis. Hãy bổ sung .env; không có dữ liệu được seed.")
        return
    try:
        db.ping()
        print(seed(db, args.carts, args.update))
        print("Sản phẩm thực tế:", db.scard("products:all"))
        print("Số danh mục mẫu:", sum(db.exists("products:category:" + c) for c in CATEGORIES))
        print("Số giỏ mẫu hiện có:", sum(db.exists("cart:" + u) for u in ["demo","user001","user002","user003"]))
    except RedisError:
        print("Không thể kết nối hoặc seed Redis. Kiểm tra cấu hình và mạng.")
        raise SystemExit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

