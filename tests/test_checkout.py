import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local
from unittest.mock import patch

import fakeredis
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError
from backend.main import app
from backend.api import database
from backend.checkout import checkout
from backend.seed import seed


@pytest.fixture
def env():
    db=fakeredis.FakeRedis(decode_responses=True)
    seed(db)
    app.dependency_overrides[database]=lambda:db
    with TestClient(app) as c:
        yield db,c
    app.dependency_overrides.clear()


def buy(c,user="test",key="request_0001"):
    return c.post(f"/api/cart/{user}/checkout",json={"idempotency_key":key,"confirmed":True})


def test_cart_never_changes_stock(env):
    db,c=env
    for method,path,body in [
        ("POST","/items",{"product_id":"SP001","quantity":99}),
        ("PATCH","/items/SP001",{"quantity":50}),
        ("DELETE","/items/SP001",None),
        ("POST","/items",{"product_id":"SP001","quantity":2}),
        ("DELETE","",None),
    ]:
        assert c.request(method,"/api/cart/test"+path,json=body).status_code==200
        assert db.hget("product:SP001","stock")=="20"


@pytest.mark.parametrize("items", [{"SP001":2},{"SP001":2,"SP005":3}])
def test_success(env,items):
    db,c=env
    db.hset("cart:test",mapping=items)
    r=buy(c)
    assert r.status_code==200
    o=r.json()
    assert o["status"]=="CONFIRMED_DEMO"
    assert not db.exists("cart:test")
    total=0
    for pid,q in items.items():
        assert int(db.hget("product:"+pid,"stock"))==20-q
        total+=int(db.hget("product:"+pid,"price_vnd"))*q
    assert o["total_vnd"]==total
    key="order:"+o["order_id"]
    assert db.type(key)=="hash" and db.ttl(key)==-1
    assert db.type(key+":items")=="hash" and db.ttl(key+":items")==-1
    assert len(db.hgetall(key+":items"))==len(items)
    assert c.get("/api/cart/test/orders/"+o["order_id"]).json()==o
    assert c.get("/api/cart/other/orders/"+o["order_id"]).status_code==404
    db.hset("product:SP001","price_vnd",1)
    assert c.get("/api/cart/test/orders/"+o["order_id"]).json()["total_vnd"]==total
    assert buy(c).json()==o
    assert len(list(db.scan_iter("order:*:items")))==1


def test_insufficient_all_or_nothing(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2,"SP002":99})
    db.expire("cart:test",1000)
    before=db.hgetall("cart:test")
    r=buy(c)
    assert r.status_code==409 and "SP002" in r.json()["detail"]
    assert db.hgetall("cart:test")==before
    assert db.hget("product:SP001","stock")=="20"
    assert db.hget("product:SP002","stock")=="21"
    assert not list(db.scan_iter("order:*"))
    assert 990<db.ttl("cart:test")<=1000


def test_missing_product(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2,"SP002":1})
    db.delete("product:SP002")
    assert buy(c).status_code==409
    assert db.hget("product:SP001","stock")=="20"
    assert db.hlen("cart:test")==2
    assert not list(db.scan_iter("order:*"))


def test_current_price(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2})
    db.hset("product:SP001","price_vnd",123456)
    assert buy(c).json()["total_vnd"]==246912


def test_empty_and_validation(env):
    _,c=env
    assert buy(c).status_code==400
    for body in [{},{"confirmed":False,"idempotency_key":"request000"},{"confirmed":True,"idempotency_key":"short"},{"confirmed":True,"idempotency_key":"request000","total_vnd":1}]:
        assert c.post("/api/cart/test/checkout",json=body).status_code==422


def test_retry_after_unknown_success_does_not_clear_new_cart(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2})
    o=buy(c).json()
    db.hset("cart:test",mapping={"SP002":1})
    assert buy(c).json()==o
    assert db.hgetall("cart:test")=={"SP002":"1"}
    assert db.hget("product:SP001","stock")=="18"


@pytest.mark.parametrize("same_request",[False,True])
def test_concurrent_checkout(env,same_request):
    db,_=env
    db.hset("product:SP001","stock",3)
    db.hset("cart:a",mapping={"SP001":2})
    if not same_request:
        db.hset("cart:b",mapping={"SP001":2})
    gate=Barrier(2)
    thread_state=local()
    cls=type(db.pipeline())
    original=cls.execute
    def execute(pipe,*args,**kwargs):
        if not getattr(thread_state,"entered",False):
            thread_state.entered=True
            gate.wait(timeout=5)
        return original(pipe,*args,**kwargs)
    def run(user):
        try:return checkout(db,user,"same_request")
        except HTTPException as e:return e.status_code
    with patch.object(cls,"execute",execute):
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(run,"a")
            b=pool.submit(run,"a" if same_request else "b")
            results=[a.result(),b.result()]
    assert db.hget("product:SP001","stock")=="1"
    assert len(list(db.scan_iter("order:*:items")))==1
    if same_request:
        assert results[0]["order_id"]==results[1]["order_id"]
    else:
        assert sorted(isinstance(r,dict) for r in results)==[False,True]
        assert 409 in results


def test_connection_loss(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2})
    with patch.object(db,"pipeline",side_effect=ConnectionError("secret")):
        r=buy(c)
    assert r.status_code==503 and "secret" not in r.text
    assert db.hget("product:SP001","stock")=="20"
    assert db.exists("cart:test")


def test_change_during_checkout_retries(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2})
    cls=type(db.pipeline())
    original=cls.execute
    changed=False
    def execute(pipe,*args,**kwargs):
        nonlocal changed
        if not changed:
            changed=True
            db.hset("product:SP001","stock",1)
        return original(pipe,*args,**kwargs)
    with patch.object(cls,"execute",execute):
        assert buy(c).status_code==409
    assert db.hget("product:SP001","stock")=="1"
    assert db.hgetall("cart:test")=={"SP001":"2"}
    assert not list(db.scan_iter("order:*"))


def test_response_lost_after_commit_replay(env):
    db,c=env
    db.hset("cart:test",mapping={"SP001":2})
    cls=type(db.pipeline())
    original=cls.execute
    def execute(pipe,*args,**kwargs):
        original(pipe,*args,**kwargs)
        raise ConnectionError("response lost")
    with patch.object(cls,"execute",execute):
        assert buy(c).status_code==503
    assert db.hget("product:SP001","stock")=="18"
    assert not db.exists("cart:test")
    r=buy(c)
    assert r.status_code==200
    assert db.hget("product:SP001","stock")=="18"
    assert len(list(db.scan_iter("order:*:items")))==1


@pytest.mark.parametrize("quantity",["0","-1","100","bad"])
def test_corrupt_cart_rejected(env,quantity):
    db,c=env
    db.hset("cart:test",mapping={"SP001":quantity})
    assert buy(c).status_code==409
    assert db.hget("product:SP001","stock")=="20"

