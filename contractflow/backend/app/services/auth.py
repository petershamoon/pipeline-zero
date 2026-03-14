"""Local auth and server-side session management."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.models.user_session import UserSession


class AuthError(RuntimeError):
    pass


_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except VerifyMismatchError:
        return False


def _hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


async def authenticate_local(db: AsyncSession, *, email: str, password: str) -> User:
    user = (
        await db.execute(
            select(User).where(User.email.ilike(email.strip())).limit(1)
        )
    ).scalar_one_or_none()
    if user is None or not user.password_hash or not verify_password(password, user.password_hash):
        raise AuthError("Invalid credentials")
    if not user.is_active:
        raise AuthError("User is inactive")
    return user


async def create_session(db: AsyncSession, *, user: User, settings: Settings) -> tuple[str, str]:
    raw_session_id = _generate_token()
    raw_csrf = _generate_token()
    ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)

    db.add(
        UserSession(
            user_id=user.id,
            session_id_hash=_hash_token(raw_session_id),
            csrf_token_hash=_hash_token(raw_csrf),
            expires_at=datetime.now(timezone.utc) + ttl,
        )
    )
    await db.flush()
    return raw_session_id, raw_csrf


async def get_session_with_user(db: AsyncSession, *, raw_session_id: str) -> tuple[UserSession, User]:
    session_hash = _hash_token(raw_session_id)
    row = (
        await db.execute(
            select(UserSession, User)
            .join(User, User.id == UserSession.user_id)
            .where(UserSession.session_id_hash == session_hash)
            .limit(1)
        )
    ).one_or_none()
    if row is None:
        raise AuthError("Invalid session")

    session_obj, user = row
    now = datetime.now(timezone.utc)
    if session_obj.expires_at <= now:
        await db.delete(session_obj)
        raise AuthError("Session expired")
    if not user.is_active:
        raise AuthError("User inactive")
    return session_obj, user


async def rotate_session(db: AsyncSession, *, session_obj: UserSession, settings: Settings) -> str:
    raw_session_id = _generate_token()
    ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)

    session_obj.session_id_hash = _hash_token(raw_session_id)
    session_obj.expires_at = datetime.now(timezone.utc) + ttl
    await db.flush()
    return raw_session_id


def verify_csrf_token(*, raw_csrf_cookie: str | None, raw_csrf_header: str | None, session_obj: UserSession) -> bool:
    if not raw_csrf_cookie or not raw_csrf_header:
        return False
    if raw_csrf_cookie != raw_csrf_header:
        return False
    return _hash_token(raw_csrf_cookie) == session_obj.csrf_token_hash


async def destroy_session(db: AsyncSession, *, raw_session_id: str) -> None:
    await db.execute(
        delete(UserSession).where(UserSession.session_id_hash == _hash_token(raw_session_id))
    )


async def destroy_session_by_id(db: AsyncSession, *, session_id: uuid.UUID) -> None:
    await db.execute(delete(UserSession).where(UserSession.id == session_id))


async def purge_expired_sessions(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(delete(UserSession).where(UserSession.expires_at < now))
    return result.rowcount or 0
