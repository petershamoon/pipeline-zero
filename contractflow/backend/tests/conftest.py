"""Shared pytest fixtures for ContractFlow backend tests."""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.database import get_db_session
from app.main import create_app


def get_test_settings() -> Settings:
    """Settings override for tests."""
    return Settings(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql+asyncpg://contractflow:testpass@localhost:5433/contractflow_test",
        REDIS_URL="redis://localhost:6380/0",
        ALLOWED_ORIGINS="http://localhost:3000",
        AZURE_STORAGE_ACCOUNT_URL="http://127.0.0.1:10002/devstoreaccount1",
        AZURE_STORAGE_CONTAINER="contracts-test",
        CSRF_SECRET="test-csrf-secret",
    )


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    settings = get_test_settings()
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    yield engine


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test database session."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with DB session override."""
    app = create_app()

    async def override_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
