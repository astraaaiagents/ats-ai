import time

import redis.asyncio as aioredis
from fastapi import Depends, Request, Response, status

from app.config import settings
from app.middleware.error_handler import AppException

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


async def _check_sliding_window(
    redis: aioredis.Redis, key: str, max_requests: int, window_seconds: int
) -> tuple[bool, int]:
    now = time.time()
    window_start = now - window_seconds
    await redis.zremrangebyscore(key, 0, window_start)
    count = await redis.zcard(key)
    allowed = int(count) < max_requests
    if allowed:
        pipe = await redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, int(window_seconds * 2))
        await pipe.execute()
    return allowed, count


async def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")


async def get_user_id(request: Request) -> str:
    return request.headers.get("X-User-ID", "anonymous")


async def rate_limiter(
    request: Request,
    response: Response,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id),
) -> None:
    try:
        redis = await get_redis_client()
    except (ConnectionError, OSError) as e:
        raise AppException(
            code="RATE_LIMIT_SERVICE_UNAVAILABLE",
            message="Rate limiting service unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    burst_key = f"rate:burst:{user_id}"
    burst_allowed, _ = await _check_sliding_window(redis, burst_key, settings.rate_limit_burst_per_second, 1)
    if not burst_allowed:
        raise AppException(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests - burst limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    user_key = f"rate:user:{user_id}"
    user_allowed, user_count = await _check_sliding_window(redis, user_key, settings.rate_limit_user_per_minute, 60)
    if not user_allowed:
        raise AppException(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests - user rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    tenant_key = f"rate:tenant:{tenant_id}"
    tenant_allowed, _ = await _check_sliding_window(redis, tenant_key, settings.rate_limit_tenant_per_minute, 60)
    if not tenant_allowed:
        raise AppException(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests - tenant rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    remaining = max(0, settings.rate_limit_user_per_minute - user_count)
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_user_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
