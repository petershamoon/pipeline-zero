"""Health check endpoints.

Mounted at root (not under /api/v1) for infrastructure probes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session

health_router = APIRouter(tags=["health"])


@health_router.get("/health/live")
async def liveness():
    """Liveness probe: confirms the process is running."""
    return {"status": "ok"}


@health_router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db_session)):
    """Readiness probe: verifies DB and Redis connectivity."""
    await db.execute(text("SELECT 1"))
    settings = get_settings()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.ping()
    await redis.aclose()
    return {"status": "ready"}
