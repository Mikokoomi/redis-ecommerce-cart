import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def redis_settings():
    host = os.getenv("REDIS_HOST", "").strip()
    port = os.getenv("REDIS_PORT", "").strip()
    password = os.getenv("REDIS_PASSWORD", "")
    if not host or not port or not password:
        return None
    try:
        port_number = int(port)
        if not 1 <= port_number <= 65535:
            return None
    except ValueError:
        return None
    return {
        "host": host,
        "port": port_number,
        "username": os.getenv("REDIS_USERNAME", "default"),
        "password": password,
        "ssl": os.getenv("REDIS_SSL", "false").lower() in {"true", "1", "yes"},
        "socket_connect_timeout": 3,
        "socket_timeout": 3,
        "decode_responses": True,
    }
