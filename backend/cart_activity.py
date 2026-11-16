import time

INDEX = "carts:updated"
STREAM = "events:cart"


def watch_activity(pipe):
    from fastapi import HTTPException
    pipe.watch(INDEX, STREAM)
    if pipe.type(INDEX) not in ("none", "zset") or pipe.type(STREAM) not in ("none", "stream"):
        raise HTTPException(503, "Chỉ mục hoặc lịch sử giỏ hàng không hợp lệ.")


def activity(pipe, user_id, action, product_id="", quantity="", remove=False):
    if remove:
        pipe.zrem(INDEX, user_id)
    else:
        pipe.zadd(INDEX, {user_id: time.time()})
    pipe.xadd(STREAM, {"action": action, "user_id": user_id,
                      "product_id": product_id, "quantity": str(quantity)},
              maxlen=1000, approximate=False)


def recent_carts(db):
    result = []
    for user_id, updated in db.zrevrange(INDEX, 0, -1, withscores=True):
        if db.exists("cart:" + user_id):
            result.append({"user_id": user_id, "updated_at": updated})
        else:
            with db.pipeline() as pipe:
                from redis.exceptions import WatchError
                try:
                    pipe.watch("cart:" + user_id)
                    if not pipe.exists("cart:" + user_id):
                        pipe.multi()
                        pipe.zrem(INDEX, user_id)
                        pipe.execute()
                except WatchError:
                    pass
    return result
