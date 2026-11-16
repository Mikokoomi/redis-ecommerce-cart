from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError

from .redis_client import create_redis_client
from .api import router
from .auth import router as auth_router
app = FastAPI(title="Redis E-Commerce Cart")
app.include_router(router)
app.include_router(auth_router)


@app.exception_handler(RedisError)
async def redis_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Redis tạm thời không khả dụng. Vui lòng thử lại."})
frontend = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=frontend / "css"), name="css")
app.mount("/js", StaticFiles(directory=frontend / "js"), name="js")
app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(frontend / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/redis")
def redis_health():
    client = create_redis_client()
    if client is None:
        return JSONResponse(status_code=503, content={"status": "unavailable", "detail": "Redis chưa được cấu hình đầy đủ."})
    try:
        client.ping()
        return {"status": "ok"}
    except RedisError:
        return JSONResponse(status_code=503, content={"status": "unavailable", "detail": "Không thể kết nối Redis."})
    finally:
        client.close()
