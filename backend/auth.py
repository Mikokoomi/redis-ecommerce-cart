
"""Registration and cookie-based login for RedisCart.

Step 1: Authentication only.
Existing cart APIs are not protected yet.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from redis.exceptions import WatchError

from .redis_client import create_redis_client

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

COOKIE_NAME = "rediscart_session"
SESSION_TTL_SECONDS = 24 * 60 * 60
PBKDF2_ITERATIONS = 350_000

class RegisterData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    email: str = Field(
        min_length=6,
        max_length=254,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    )
    password: str = Field(min_length=8, max_length=128)

class LoginData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str

def auth_database():
    db = create_redis_client()

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Redis chưa được cấu hình."
        )

    try:
        yield db
    finally:
        db.close()

def _email(value: str) -> str:
    return value.strip().lower()

def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )

    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )

def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, expected = stored.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        if int(rounds) != PBKDF2_ITERATIONS:
            return False

        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(rounds)
        )

        return hmac.compare_digest(
            calculated,
            bytes.fromhex(expected)
        )

    except (ValueError, TypeError):
        return False

def _public_user(data: dict) -> dict:
    return {
        "user_id": data["user_id"],
        "name": data["name"],
        "email": data["email"],
        "role": data["role"]
    }

def _session_key(raw_token: str) -> str:
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return "session:" + token_hash

def _login_session(
    db,
    response: Response,
    request: Request,
    user_id: str
) -> None:

    raw_token = secrets.token_urlsafe(32)

    db.setex(
        _session_key(raw_token),
        SESSION_TTL_SECONDS,
        user_id
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/"
    )

def current_user(
    request: Request,
    db=Depends(auth_database)
) -> dict:

    raw_token = request.cookies.get(COOKIE_NAME, "")

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Bạn chưa đăng nhập."
        )

    user_id = db.get(_session_key(raw_token))

    user = (
        db.hgetall("user:" + user_id)
        if user_id
        else None
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn."
        )

    return _public_user(user)

@router.post("/register", status_code=201)
def register(
    body: RegisterData,
    db=Depends(auth_database)
):
    email = _email(body.email)
    email_key = "user:email:" + email
    user_id = uuid4().hex

    user = {
        "user_id": user_id,
        "name": body.name.strip(),
        "email": email,
        "password_hash": _hash_password(body.password),
        "role": "customer",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    for _ in range(3):
        with db.pipeline() as pipe:
            try:
                pipe.watch(email_key)

                if pipe.exists(email_key):
                    raise HTTPException(
                        status_code=409,
                        detail="Email đã được đăng ký."
                    )

                pipe.multi()

                pipe.set(email_key, user_id)

                pipe.hset(
                    "user:" + user_id,
                    mapping=user
                )

                pipe.execute()

                return _public_user(user)

            except WatchError:
                continue

    raise HTTPException(
        status_code=409,
        detail="Không thể tạo tài khoản lúc này. Vui lòng thử lại."
    )

@router.post("/login")
def login(
    body: LoginData,
    request: Request,
    response: Response,
    db=Depends(auth_database)
):
    user_id = db.get(
        "user:email:" + _email(body.email)
    )

    user = (
        db.hgetall("user:" + user_id)
        if user_id
        else {}
    )

    if not user or not _verify_password(
        body.password,
        user.get("password_hash", "")
    ):
        raise HTTPException(
            status_code=401,
            detail="Email hoặc mật khẩu không đúng."
        )

    _login_session(
        db,
        response,
        request,
        user_id
    )

    return _public_user(user)

@router.get("/me")
def me(user=Depends(current_user)):
    return user

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db=Depends(auth_database)
):
    token = request.cookies.get(COOKIE_NAME)

    if token:
        db.delete(_session_key(token))

    response.delete_cookie(
        COOKIE_NAME,
        path="/"
    )

    return {"status": "ok"}