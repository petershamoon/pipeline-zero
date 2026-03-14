"""Distributed rate limiter with Redis and in-memory fallback."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import get_settings


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimiter:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._redis: Redis | None = None
        self._fallback: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> Redis | None:
        if self._redis is not None:
            return self._redis
        try:
            self._redis = Redis.from_url(self._settings.REDIS_URL, decode_responses=True)
            await self._redis.ping()
            return self._redis
        except Exception:
            self._redis = None
            return None

    async def allow(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        redis_client = await self._get_redis()
        if redis_client is not None:
            return await self._allow_with_redis(key, limit=limit, window_seconds=window_seconds)
        return await self._allow_in_memory(key, limit=limit, window_seconds=window_seconds)

    async def _allow_with_redis(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        bucket = f"rl:{key}:{int(time.time() // window_seconds)}"
        count = int(await self._redis.incr(bucket))  # type: ignore[union-attr]
        if count == 1:
            await self._redis.expire(bucket, window_seconds)  # type: ignore[union-attr]
        if count <= limit:
            return RateLimitResult(allowed=True, retry_after_seconds=0)
        ttl = await self._redis.ttl(bucket)  # type: ignore[union-attr]
        retry_after = max(int(ttl), 1)
        return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

    async def _allow_in_memory(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            samples = self._fallback.setdefault(key, [])
            samples[:] = [stamp for stamp in samples if stamp >= window_start]
            if len(samples) >= limit:
                retry_after = int(max(samples[0] + window_seconds - now, 1))
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)
            samples.append(now)
            return RateLimitResult(allowed=True, retry_after_seconds=0)


rate_limiter = RateLimiter()
