"""Integration-test fixtures for authenticated requests."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User
from app.models.user_session import UserSession
from app.services.auth import _hash_token, hash_password


async def create_test_department(
    db: AsyncSession,
    *,
    name: str = "Test Department",
    description: str | None = None,
) -> Department:
    """Insert a department and return it."""
    dept = Department(name=name, description=description, is_active=True)
    db.add(dept)
    await db.flush()
    return dept


async def create_test_user(
    db: AsyncSession,
    *,
    email: str = "testuser@example.com",
    display_name: str = "Test User",
    role: UserRole = UserRole.CONTRIBUTOR,
    password: str = "test-password-123",
    department_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> User:
    """Insert a user with a hashed password and return it."""
    user = User(
        email=email,
        display_name=display_name,
        role=role,
        password_hash=hash_password(password),
        department_id=department_id,
        is_active=is_active,
    )
    db.add(user)
    await db.flush()
    return user


async def create_authenticated_session(
    db: AsyncSession,
    user: User,
) -> tuple[str, str]:
    """Create a session row in the DB and return (raw_session_id, raw_csrf_token).

    The caller should set cookies on the httpx client:
        cf_session = raw_session_id
        cf_csrf   = raw_csrf_token
    and the X-CSRF-Token header = raw_csrf_token for mutating requests.
    """
    raw_session_id = f"test-session-{uuid.uuid4().hex}"
    raw_csrf = f"test-csrf-{uuid.uuid4().hex}"

    session_obj = UserSession(
        user_id=user.id,
        session_id_hash=_hash_token(raw_session_id),
        csrf_token_hash=_hash_token(raw_csrf),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(session_obj)
    await db.flush()
    return raw_session_id, raw_csrf


def set_auth_cookies(
    client: AsyncClient,
    raw_session_id: str,
    raw_csrf: str,
) -> None:
    """Set auth cookies on the httpx client for subsequent requests."""
    client.cookies.set("cf_session", raw_session_id)
    client.cookies.set("cf_csrf", raw_csrf)


def auth_headers(raw_csrf: str) -> dict[str, str]:
    """Return the X-CSRF-Token header required for mutating requests."""
    return {"X-CSRF-Token": raw_csrf}
