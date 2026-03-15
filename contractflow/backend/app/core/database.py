"""Database engine and session management."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def _create_engine():
    settings = get_settings()
    # asyncpg does not accept ?sslmode=require as a URL query param — it must be
    # passed via connect_args as ssl=True (or an ssl.SSLContext).
    # database_url_async already strips the sslmode param from the URL;
    # here we detect whether SSL was originally requested and pass it via
    # connect_args so the TLS handshake with Azure PostgreSQL still works.
    raw_url = settings.DATABASE_URL
    needs_ssl = "sslmode=require" in raw_url
    connect_args: dict = {}
    if needs_ssl:
        connect_args["ssl"] = True

    return create_async_engine(
        settings.database_url_async,
        pool_pre_ping=True,
        echo=not settings.is_production,
        connect_args=connect_args,
    )


engine = _create_engine()
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a transactional async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
