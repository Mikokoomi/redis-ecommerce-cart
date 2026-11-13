import copy
import json
from unittest.mock import patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from backend.api import database
from backend.main import app
from backend.catalog_import import (load_catalog, import_catalog, backup_catalog,
                                    snapshot_catalog, verify_images, CATEGORIES)
from backend.seed import seed


@pytest.fixture
def env():
    db=fakeredis.FakeRedis(decode_responses=True)
    seed(db,carts=True)
    db.hset("order:existing",mapping={"order_id":"existing","total_vnd":9000})
    db.hset("order:existing:items",mapping={"SP001":"snapshot"})
    db.set("checkout:request:existing","existing")
    db.set("unrelated","keep")
    return db,load_catalog()


def values(db):
    return {key:db.dump(key) for key in db.scan_iter()}


def test_input_has_20_real_models(env):
    _,payload=env
    assert len(payload["products"])==20
    assert payload["products"][0]["name"].startswith("Samsung")
    assert payload["products"][19]["brand"]=="UGREEN"


def test_dry_run_no_writes(env):
    db,payload=env
    before=values(db)
    report=import_catalog(db,payload,dry_run=True)
    assert len(report)==20
    assert all(r["action"]=="update" and r["stock"]=="preserved" for r in report)
    assert before==values(db)


def test_backup_only_catalogue(env,tmp_path):
    db,_=env
    file=backup_catalog(db,tmp_path)
    data=json.loads(file.read_text(encoding="utf-8"))
    assert len(data["hashes"])==20
    assert len(data["sets"])==6
    assert all(k.startswith("product:") for k in data["hashes"])
    assert all(k=="products:all" or k.startswith("products:category:") for k in data["sets"])
    assert "order:existing" not in file.read_text(encoding="utf-8")
    assert backup_catalog(db,tmp_path)!=file


def test_import_preserves_stock_and_other_data(env):
    db,payload=env
    db.hset("product:SP001","stock",0)
    db.hset("product:SP001","custom_field","keep")
    before=values(db)
    stocks={p["id"]:db.hget("product:"+p["id"],"stock") for p in payload["products"]}
    import_catalog(db,payload,dry_run=False)
    for p in payload["products"]:
        data=db.hgetall("product:"+p["id"])
        assert data["stock"]==stocks[p["id"]]
        assert data["name"]==p["name"]
        assert data["price_vnd"]==str(p["price_vnd"])
        assert json.loads(data["specs"])==p["specs"]
        assert data["image"]==f'/assets/images/products/{p["id"]}.webp'
        assert db.ttl("product:"+p["id"])==-1
    for key,value in before.items():
        if not key.startswith("product:") and not key.startswith("products:"):
            assert db.dump(key)==value
    assert db.hget("product:SP001","custom_field")=="keep"
    assert db.scard("products:all")==20
    assert all(db.scard("products:category:"+slug)==4 for slug in CATEGORIES.values())
    assert all(r["action"]=="unchanged" for r in import_catalog(db,payload,dry_run=False))


def test_new_product_initializes_stock_only_once(env):
    db,payload=env
    db.delete("product:SP020")
    import_catalog(db,payload,False)
    assert db.hget("product:SP020","stock")=="39"
    db.hset("product:SP020","stock",2)
    import_catalog(db,payload,False)
    assert db.hget("product:SP020","stock")=="2"


def test_categories_repaired_without_deleting_other_members(env):
    db,payload=env
    db.sadd("products:category:legacy","SP001","external")
    db.hset("product:SP001","category","legacy")
    import_catalog(db,payload,False)
    assert db.smembers("products:category:legacy")=={"external"}
    assert db.sismember("products:category:dien-thoai","SP001")


@pytest.mark.parametrize("bad_key",["product:SP010","products:all","products:category:laptop"])
def test_wrong_type_preflight_no_partial_import(env,bad_key):
    db,payload=env
    db.delete(bad_key)
    db.set(bad_key,"wrong")
    before=values(db)
    with pytest.raises(ValueError):
        import_catalog(db,payload,False)
    assert values(db)==before


def test_stock_changed_concurrently_is_preserved(env):
    db,payload=env
    cls=type(db.pipeline())
    execute=cls.execute
    changed=False
    def racing(pipe,*args,**kwargs):
        nonlocal changed
        if not changed:
            changed=True
            db.hset("product:SP001","stock",3)
        return execute(pipe,*args,**kwargs)
    with patch.object(cls,"execute",racing):
        import_catalog(db,payload,False)
    assert db.hget("product:SP001","stock")=="3"


def test_stock_corrupt_aborts(env):
    db,payload=env
    db.hset("product:SP001","stock","bad")
    before=values(db)
    with pytest.raises(ValueError):
        import_catalog(db,payload,False)
    assert values(db)==before


@pytest.mark.parametrize("mutation",["duplicate","category","negative","specs"])
def test_input_validation(tmp_path,mutation):
    p=load_catalog()
    if mutation=="duplicate":p["products"][1]["id"]="SP001"
    if mutation=="category":p["products"][0]["category"]="unknown"
    if mutation=="negative":p["products"][0]["price_vnd"]=-1
    if mutation=="specs":p["products"][0]["specs"]=[]
    path=tmp_path/"invalid.json"
    path.write_text(json.dumps(p),encoding="utf-8")
    with pytest.raises(ValueError):load_catalog(path)


def test_images_decoded_and_matched_manifest():
    verify_images(load_catalog()["products"])


def test_imported_api_and_cart(env):
    db,payload=env
    import_catalog(db,payload,False)
    app.dependency_overrides[database]=lambda:db
    try:
        with TestClient(app) as c:
            assert len(c.get("/api/products").json())==20
            for slug in CATEGORIES.values():
                assert len(c.get("/api/products",params={"category":slug}).json())==4
            p=c.get("/api/products/SP001").json()
            assert p["specs"]["ram"]=="8GB"
            assert p["brand"]=="Samsung"
            before=db.hget("product:SP001","stock")
            assert c.post("/api/cart/import_test/items",json={"product_id":"SP001","quantity":2}).status_code==200
            assert db.hget("product:SP001","stock")==before
            for product in payload["products"]:
                assert c.get(f'/assets/images/products/{product["id"]}.webp').status_code==200
    finally:
        app.dependency_overrides.clear()

