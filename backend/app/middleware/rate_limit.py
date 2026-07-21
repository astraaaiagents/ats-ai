import time

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status

from app.config import settings

_redis: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis_client() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def _check_sliding_window(redis: aioredis.Redis, key: str, max_requests: int, window_seconds: int) -> bool:
    now = time.time()
    window_start = now - window_seconds
    pipe = await redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, int(window_seconds * 2))
    results = await pipe.execute()
    count = results[1]
    return int(count) < max_requests


async def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")


async def get_user_id(request: Request) -> str:
    return request.headers.get("X-User-ID", "anonymous")


async def rate_limiter(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id),
) -> None:
    try:
        redis = await get_redis_client()
    except (ConnectionError, OSError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service unavailable",
        )

    burst_key = f"rate:burst:{user_id}"
    if not await _check_sliding_window(redis, burst_key, settings.rate_limit_burst_per_second, 1):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests - burst limit exceeded",
        )

    user_key = f"rate:user:{user_id}"
    if not await _check_sliding_window(redis, user_key, settings.rate_limit_user_per_minute, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests - user rate limit exceeded",
        )

    tenant_key = f"rate:tenant:{tenant_id}"
    if not await _check_sliding_window(redis, tenant_key, settings.rate_limit_tenant_per_minute, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests - tenant rate limit exceeded",
        )
