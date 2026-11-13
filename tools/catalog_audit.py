"""Đối chiếu catalogue và dữ liệu ngoài catalogue; không in dữ liệu giỏ/đơn."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.catalog_import import load_catalog, CATEGORIES
from backend.redis_client import create_redis_client

def protected(db):
    records={}
    for prefix in ["cart:*","order:*","checkout:request:*"]:
        for key in db.scan_iter(match=prefix,count=100):
            records[hashlib.sha256(key.encode()).hexdigest()]={
                "digest":hashlib.sha256(db.dump(key)).hexdigest(),
                "expires":db.pttl(key)>=0,
            }
    return records

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--record",action="store_true")
    args=parser.parse_args()
    db=create_redis_client()
    if db is None:raise SystemExit("Missing Redis config")
    try:
        assert db.ping()
        path=ROOT/"work/catalog-protected-before.json"
        if args.record:
            state={"protected":protected(db),"stock":{p["id"]:db.hget("product:"+p["id"],"stock") for p in load_catalog()["products"]}}
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(state,indent=2),encoding="utf-8")
            print("PROTECTED_BASELINE_RECORDED",len(state["protected"]))
            return
        state=json.loads(path.read_text(encoding="utf-8"))
        after=protected(db)
        changed=[k for k,v in state["protected"].items() if k in after and after[k]["digest"]!=v["digest"]]
        missing_persistent=[k for k,v in state["protected"].items() if k not in after and not v["expires"]]
        assert not changed, "Existing cart/order value changed."
        assert not missing_persistent,"Persistent protected key missing."
        assert not set(after)-set(state["protected"]),"Unexpected protected key created."
        for p in load_catalog()["products"]:
            data=db.hgetall("product:"+p["id"])
            assert data["name"]==p["name"]
            assert int(data["price_vnd"])==p["price_vnd"]
            assert data["category"]==CATEGORIES[p["category"]]
            assert json.loads(data["specs"])==p["specs"]
            assert data["image"]==f'/assets/images/products/{p["id"]}.webp'
            if state["stock"][p["id"]] is not None:
                assert data["stock"]==state["stock"][p["id"]], "Stock changed."
            assert db.ttl("product:"+p["id"])==-1
        print("CATALOGUE_HASHES",sum(1 for _ in db.scan_iter(match="product:*",count=100)))
        print("ALL_SET",db.scard("products:all"))
        print("CATEGORY_COUNTS",{c:db.scard("products:category:"+c) for c in CATEGORIES.values()})
        print("EXISTING_STOCK_PRESERVED",True)
        print("PROTECTED_DATA_UNCHANGED",len(state["protected"]))
        print("EXPIRED_TTL_KEYS",sum(k not in after for k,v in state["protected"].items() if v["expires"]))
    finally:db.close()

if __name__=="__main__":main()

