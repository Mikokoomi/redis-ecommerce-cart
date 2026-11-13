import pytest
import fakeredis
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError
from backend.main import app
from backend.api import database
from backend.seed import seed, CATEGORIES

@pytest.fixture
def setup():
    db = fakeredis.FakeRedis(decode_responses=True)
    seed(db)
    app.dependency_overrides[database] = lambda: db
    with TestClient(app) as client:
        yield db, client
    app.dependency_overrides.clear()

def test_seed(setup):
    db, _ = setup
    assert db.scard("products:all") == 20
    assert len(list(db.scan_iter("product:*"))) == 20
    assert all(db.scard("products:category:"+c) == 4 for c in CATEGORIES)
    assert all(db.ttl(k) == -1 for k in db.scan_iter("product*"))

def test_seed_preserves(setup):
    db, _ = setup
    db.hset("product:SP001", "name", "Tên riêng")
    result = seed(db, carts=True)
    assert result["products"]["skipped"] == 20
    assert db.hget("product:SP001","name") == "Tên riêng"
    assert result["carts"]["created"] == 4
    db.hset("cart:demo","SP001",9)
    assert seed(db,carts=True)["carts"]["skipped"] == 4
    assert db.hget("cart:demo","SP001") == "9"
    assert 86300 < db.ttl("cart:demo") <= 86400
    assert seed(db,update=True)["products"]["updated"] == 20

def test_products(setup):
    _, c = setup
    assert len(c.get("/api/products").json()) == 20
    for category in CATEGORIES:
        assert len(c.get("/api/products",params={"category":category}).json()) == 4
    assert c.get("/api/products/SP001").json()["price_vnd"] == 4500000
    assert c.get("/api/products/SP999").status_code == 404

def test_cart_flow(setup):
    db,c = setup
    path="/api/cart/test"
    assert c.get(path).json()["items"] == []
    assert c.post(path+"/items",json={"product_id":"SP001","quantity":2}).status_code == 200
    d=c.post(path+"/items",json={"product_id":"SP001","quantity":3}).json()
    assert d["total_quantity"] == 5
    assert d["total_vnd"] == 22500000
    db.expire("cart:test",5)
    assert c.patch(path+"/items/SP001",json={"quantity":8}).json()["total_quantity"] == 8
    assert 86300 < db.ttl("cart:test") <= 86400
    assert c.get(path).json()["total_quantity"] == 8
    assert c.patch(path+"/items/SP001",json={"quantity":0}).json()["items"] == []
    c.post(path+"/items",json={"product_id":"SP001","quantity":1})
    assert c.delete(path+"/items/SP001").json()["items"] == []
    c.post(path+"/items",json={"product_id":"SP005","quantity":1})
    assert c.delete(path).json()["items"] == []
    assert db.exists("cart:test") == 0

@pytest.mark.parametrize("quantity",[-1,100,1.5,"2",True])
def test_invalid_quantity(setup,quantity):
    _,c=setup
    assert c.post("/api/cart/test/items",json={"product_id":"SP001","quantity":quantity}).status_code == 422

def test_limit_and_price(setup):
    _,c=setup
    path="/api/cart/test/items"
    c.post(path,json={"product_id":"SP001","quantity":99})
    assert c.post(path,json={"product_id":"SP001","quantity":1}).status_code == 422
    assert c.post(path,json={"product_id":"SP001","quantity":1,"price_vnd":1}).status_code == 422
    assert c.post(path,json={"product_id":"SP999","quantity":1}).status_code == 404

def test_unavailable(setup):
    _,c=setup
    class Broken:
        def smembers(self,key):
            raise ConnectionError("secret must not leak")
    app.dependency_overrides[database]=lambda:Broken()
    r=c.get("/api/products")
    assert r.status_code == 503
    assert "secret" not in r.text

def test_static(setup):
    _,c=setup
    for path in ["/","/health","/css/style.css","/js/app.js","/assets/laptop.svg"]:
        assert c.get(path).status_code == 200

