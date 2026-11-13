"""Nhập catalogue được cung cấp; không thao tác giỏ, đơn hoặc stock hiện có."""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from redis.exceptions import RedisError, WatchError
from .redis_client import create_redis_client

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "real_tech_catalog_for_codex/products_real_20.json"
CATEGORIES = {"Điện thoại":"dien-thoai","Laptop":"laptop","Tai nghe":"tai-nghe","Đồng hồ":"dong-ho","Phụ kiện":"phu-kien"}

def load_catalog(path=DEFAULT_INPUT):
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    rows = payload["products"]
    if len(rows) != 20 or {p["id"] for p in rows} != {f"SP{i:03}" for i in range(1,21)}:
        raise ValueError("Phải có đúng 20 mã SP001–SP020, không trùng.")
    if Counter(p["category"] for p in rows) != Counter({c:4 for c in CATEGORIES}):
        raise ValueError("Cần đủ 5 danh mục, mỗi danh mục 4 sản phẩm.")
    for p in rows:
        for key in ["name","brand","model","description"]:
            if not isinstance(p.get(key),str) or not p[key].strip():
                raise ValueError(f'{p["id"]}: thiếu {key}.')
        for key in ["price_vnd","stock_demo"]:
            if type(p.get(key)) is not int or p[key]<0:
                raise ValueError(f'{p["id"]}: {key} phải là số nguyên không âm.')
        if not isinstance(p.get("specs"),dict) or not p["specs"] or not all(isinstance(k,str) and isinstance(v,str) for k,v in p["specs"].items()):
            raise ValueError(f'{p["id"]}: specs không hợp lệ.')
        for key in ["manufacturer_url","image_url","image_source_page"]:
            if urlparse(p.get(key,"")).scheme != "https" or not urlparse(p[key]).hostname:
                raise ValueError(f'{p["id"]}: URL {key} không hợp lệ.')
    return payload

def snapshot_catalog(db):
    # SCAN giới hạn namespace catalogue, không đọc cart/order/credentials.
    hashes, sets = {}, {}
    for key in sorted(set(db.scan_iter(match="product:*",count=100))):
        if db.type(key) != "hash":
            raise ValueError("Catalogue có key không phải Hash.")
        hashes[key] = {"fields":db.hgetall(key),"pttl":db.pttl(key)}
    keys = set(db.scan_iter(match="products:category:*",count=100))
    if db.exists("products:all"):
        keys.add("products:all")
    for key in sorted(keys):
        if db.type(key) != "set":
            raise ValueError("Index catalogue không phải Set.")
        sets[key] = {"members":sorted(db.smembers(key)),"pttl":db.pttl(key)}
    return {"created_at":datetime.now(timezone.utc).isoformat(),"hashes":hashes,"sets":sets}

def backup_catalog(db,directory=None):
    directory=Path(directory or ROOT/"docs/backups")
    directory.mkdir(parents=True,exist_ok=True)
    target=directory/("catalog-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json")
    # 'x' tránh ghi đè bản sao lưu.
    with target.open("x",encoding="utf-8") as f:
        json.dump(snapshot_catalog(db),f,ensure_ascii=False,indent=2)
    return target

def metadata(p):
    manifest_path=ROOT/"docs/product-image-manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    source=manifest.get(p["id"],{})
    return {"product_id":p["id"],"name":p["name"],"brand":p["brand"],"model":p["model"],
            "description":p["description"],"price_vnd":p["price_vnd"],
            "category":CATEGORIES[p["category"]],"specs":json.dumps(p["specs"],ensure_ascii=False),
            "manufacturer_url":p["manufacturer_url"],"image_source_page":source.get("source_page",p["image_source_page"]),
            "image_origin_url":source.get("url",p["image_url"]),
            "image":f'/assets/images/products/{p["id"]}.webp',"price_kind":"illustrative"}

def verify_images(rows):
    from PIL import Image
    manifest_path=ROOT/"docs/product-image-manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for p in rows:
        path=ROOT/f'frontend/assets/images/products/{p["id"]}.webp'
        with Image.open(path) as img:
            img.load()
            if img.width<300 or img.format!="WEBP":
                raise ValueError(f'{p["id"]}: ảnh WebP nhỏ hoặc không hợp lệ.')
        if manifest.get(p["id"],{}).get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'{p["id"]}: ảnh không khớp manifest.')

def import_catalog(db,payload,dry_run=True):
    rows=payload["products"]
    category_keys=set(db.scan_iter(match="products:category:*",count=100))
    category_keys.update("products:category:"+c for c in CATEGORIES.values())
    keys=["products:all",*sorted(category_keys),*["product:"+p["id"] for p in rows]]
    for _ in range(8):
        with db.pipeline() as pipe:
            try:
                pipe.watch(*keys)
                for key in keys:
                    expected="hash" if key.startswith("product:") else "set"
                    if pipe.type(key) not in ("none",expected):
                        raise ValueError("Sai kiểu dữ liệu catalogue; đã dừng trước khi ghi.")
                plan=[]
                for p in rows:
                    key="product:"+p["id"]
                    current=pipe.hgetall(key)
                    # HSET chỉ metadata, tuyệt đối không gửi stock nếu field đã có.
                    data=metadata(p)
                    if "stock" not in current:
                        data["stock"]=p["stock_demo"]
                    elif not re.fullmatch(r"[0-9]+",current["stock"]):
                        raise ValueError(f'{p["id"]}: stock cũ không hợp lệ; không tự sửa.')
                    changed=any(str(v)!=current.get(k) for k,v in data.items())
                    plan.append({"id":p["id"],"action":"create" if not current else "update" if changed else "unchanged",
                                 "stock":"preserved" if "stock" in current else "initialize",
                                 "data":data})
                report=[{k:v for k,v in row.items() if k!="data"} for row in plan]
                if dry_run:
                    pipe.unwatch()
                    return report
                pipe.multi()
                for p,row in zip(rows,plan):
                    pid=p["id"]
                    pipe.hset("product:"+pid,mapping=row["data"])
                    # Sản phẩm/index catalogue không có TTL.
                    pipe.persist("product:"+pid)
                    pipe.sadd("products:all",pid)
                    target="products:category:"+CATEGORIES[p["category"]]
                    for category_key in sorted(category_keys):
                        if category_key!=target:
                            pipe.srem(category_key,pid)
                    pipe.sadd(target,pid)
                pipe.persist("products:all")
                for category_key in sorted(category_keys):
                    pipe.persist(category_key)
                pipe.execute()
                return report
            except WatchError:
                continue
    raise ValueError("Catalogue đang thay đổi; hết lượt retry, chưa nhập.")

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=DEFAULT_INPUT)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--backup",action="store_true")
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    db=None
    try:
        payload=load_catalog(args.input)
        db=create_redis_client()
        if db is None:
            raise ValueError("Thiếu cấu hình Redis trong .env.")
        db.ping()
        if args.backup:
            print("BACKUP",backup_catalog(db))
            return
        verify_images(payload["products"])
        if args.apply:
            print("BACKUP",backup_catalog(db))
        report=import_catalog(db,payload,dry_run=not args.apply)
        print("APPLIED" if args.apply else "DRY_RUN_NO_WRITES")
        print(json.dumps(report,ensure_ascii=False,indent=2))
        print("COUNTS",dict(Counter(row["action"] for row in report)))
    except RedisError as e:
        print("Redis error type:",type(e).__name__)
        raise SystemExit(1)
    except (ValueError,OSError,KeyError) as e:
        print("Import error:",str(e))
        raise SystemExit(1)
    finally:
        if db:
            db.close()

if __name__=="__main__":
    main()

