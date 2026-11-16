
"""Offline authentication tests using fakeredis."""

import fakeredis
import pytest

from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import auth_database

@pytest.fixture
def client():
    db = fakeredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[auth_database] = lambda: db

    with TestClient(app) as c:
        yield c, db

    app.dependency_overrides.pop(auth_database, None)

def test_register_customer_and_hash_password(client):
    c, db = client

    response = c.post(
        "/api/auth/register",
        json={
            "name": "Khách thử",
            "email": "TEST@example.com",
            "password": "safe-test-123"
        }
    )

    assert response.status_code == 201
    assert response.json()["role"] == "customer"
    assert response.json()["email"] == "test@example.com"

    user_id = response.json()["user_id"]

    stored = db.hgetall("user:" + user_id)

    assert stored["password_hash"].startswith(
        "pbkdf2_sha256$"
    )

    assert "safe-test-123" not in stored["password_hash"]

def test_register_cannot_choose_admin(client):
    c, _ = client

    response = c.post(
        "/api/auth/register",
        json={
            "name": "A B",
            "email": "a@b.test",
            "password": "safe-test-123",
            "role": "admin"
        }
    )

    assert response.status_code == 422

def test_duplicate_email(client):
    c, _ = client

    user = {
        "name": "Người dùng",
        "email": "a@b.test",
        "password": "safe-test-123"
    }

    assert c.post(
        "/api/auth/register",
        json=user
    ).status_code == 201

    assert c.post(
        "/api/auth/register",
        json=user
    ).status_code == 409

def test_login_me_logout(client):
    c, _ = client

    user = {
        "name": "Người dùng",
        "email": "a@b.test",
        "password": "safe-test-123"
    }

    assert c.get("/api/auth/me").status_code == 401

    c.post("/api/auth/register", json=user)

    wrong_login = c.post(
        "/api/auth/login",
        json={
            "email": user["email"],
            "password": "wrongpass"
        }
    )

    assert wrong_login.status_code == 401

    response = c.post(
        "/api/auth/login",
        json={
            "email": user["email"],
            "password": user["password"]
        }
    )

    assert response.status_code == 200

    assert "httponly" in response.headers[
        "set-cookie"
    ].lower()

    assert c.get("/api/auth/me").json()["role"] == "customer"

    assert c.post("/api/auth/logout").status_code == 200

    assert c.get("/api/auth/me").status_code == 401