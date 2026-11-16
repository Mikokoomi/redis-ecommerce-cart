import fakeredis
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import auth_database, COOKIE_NAME, _session_key
from backend.api import database
from backend.seed import seed
from backend.cart_activity import recent_carts
from backend.cart_activity import activity


@pytest.fixture
def env():
    db=fakeredis.FakeRedis(decode_responses=True)
    seed(db)
    app.dependency_overrides[auth_database]=lambda:db
    app.dependency_overrides[database]=lambda:db
    with TestClient(app) as c:
        yield db,c
    app.dependency_overrides.clear()


def account(c,email):
    body={"name":"Test Account","email":email,"password":"test-password-123"}
    assert c.post("/api/auth/register",json=body).status_code==201
    r=c.post("/api/auth/login",json={"email":email,"password":body["password"]})
    # Login model accepts email/password, never a role.
    assert r.status_code==200
    return r.json()["user_id"]


@pytest.mark.parametrize("method,suffix,body",[
    ("GET","",None),("POST","/items",{"product_id":"SP001","quantity":1}),
    ("PATCH","/items/SP001",{"quantity":1}),("DELETE","/items/SP001",None),
    ("DELETE","",None),("POST","/checkout",{"confirmed":True,"idempotency_key":"test-request"}),
    ("POST","/buy-now",{"confirmed":True,"idempotency_key":"test-request","product_id":"SP001","quantity":1}),
    ("GET","/orders/unknown",None)])
def test_private_routes(env,method,suffix,body):
    db,c=env
    assert c.request(method,"/api/cart/victim"+suffix,json=body).status_code==401
    account(c,"a@example.test")
    assert c.request(method,"/api/cart/victim"+suffix,json=body).status_code==403
    assert not db.exists("cart:victim")


def test_restore_switch_expire_and_activity(env):
    db,c=env
    a=account(c,"a@example.test")
    path="/api/cart/"+a
    c.post(path+"/items",json={"product_id":"SP001","quantity":2})
    assert db.hget("product:SP001","stock")=="20"
    assert db.zscore("carts:updated",a)
    assert db.xrange("events:cart")[-1][1]["action"]=="add"
    c.patch(path+"/items/SP001",json={"quantity":3})
    c.delete(path+"/items/SP001")
    assert db.xrange("events:cart")[-1][1]["action"]=="remove"
    c.post(path+"/items",json={"product_id":"SP001","quantity":2})
    c.post("/api/auth/logout")
    b=account(c,"b@example.test")
    assert c.get(path).status_code==403
    assert c.get("/api/cart/"+b).json()["items"]==[]
    c.post("/api/auth/login",json={"email":"a@example.test","password":"test-password-123"})
    assert c.get(path).json()["total_quantity"]==2
    r=c.post(path+"/buy-now",json={"product_id":"SP002","quantity":1,"confirmed":True,"idempotency_key":"direct-request"})
    assert r.status_code==200
    assert c.get(path).json()["total_quantity"]==2
    assert db.hget("product:SP002","stock")=="20"
    c.delete(path)
    assert db.xrange("events:cart")[-1][1]["action"]=="clear"
    db.zadd("carts:updated",{"expired":1})
    assert recent_carts(db)==[]
    assert db.zcard("carts:updated")==0
    token=c.cookies.get(COOKIE_NAME)
    db.delete(_session_key(token))
    assert c.get(path).status_code==401


def test_checkout_events_and_order_ownership(env):
    db,c=env
    a=account(c,"a@example.test")
    path="/api/cart/"+a
    c.post(path+"/items",json={"product_id":"SP001","quantity":1})
    body={"confirmed":True,"idempotency_key":"checkout-security"}
    r=c.post(path+"/checkout",json=body)
    assert r.status_code==200
    assert db.zscore("carts:updated",a) is None
    assert db.xrange("events:cart")[-1][1]["action"]=="checkout"
    count=db.xlen("events:cart")
    assert c.post(path+"/checkout",json=body).json()==r.json()
    assert db.xlen("events:cart")==count
    b=account(c,"b@example.test")
    assert c.get(path+"/orders/"+r.json()["order_id"]).status_code==403
    assert c.get("/api/cart/"+b+"/orders/"+r.json()["order_id"]).status_code==404
    with db.pipeline() as pipe:
        for _ in range(1002):
            activity(pipe,b,"update")
        pipe.execute()
    assert db.xlen("events:cart")==1000


def test_wrong_telemetry_type_cannot_partially_checkout(env):
    db,c=env
    a=account(c,"a@example.test")
    db.hset("cart:"+a,mapping={"SP001":2})
    db.set("events:cart","wrong")
    r=c.post("/api/cart/"+a+"/checkout",json={"confirmed":True,"idempotency_key":"wrong-type"})
    assert r.status_code==503
    assert db.hget("product:SP001","stock")=="20"
    assert db.hgetall("cart:"+a)=={"SP001":"2"}
