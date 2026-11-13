import redis

from .config import redis_settings


def create_redis_client():
    settings = redis_settings()
    if settings is None:
        return None
    return redis.Redis(**settings)
