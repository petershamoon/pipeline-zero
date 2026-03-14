"""API dependencies for auth and authorization."""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.services import auth as auth_service
from app.services import entra as entra_service

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_app_settings() -> Settings:
    return get_settings()


async def get_current_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> User:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
        try:
            principal = await entra_service.validate_bearer_token(token, settings)
        except entra_service.EntraAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        user = await entra_service.upsert_entra_user(db, principal)
        request.state.current_user = user
        return user

    raw_session = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not raw_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        session_obj, user = await auth_service.get_session_with_user(db, raw_session_id=raw_session)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if request.method not in SAFE_METHODS:
        raw_csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
        raw_csrf_header = request.headers.get("X-CSRF-Token")
        if not auth_service.verify_csrf_token(
            raw_csrf_cookie=raw_csrf_cookie,
            raw_csrf_header=raw_csrf_header,
            session_obj=session_obj,
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

    rotated_session = await auth_service.rotate_session(db, session_obj=session_obj, settings=settings)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=rotated_session,
        httponly=True,
        secure=settings.SESSION_SECURE_COOKIE or settings.is_production,
        samesite="lax",
        path="/",
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )

    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    if csrf_cookie:
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=csrf_cookie,
            httponly=False,
            secure=settings.SESSION_SECURE_COOKIE or settings.is_production,
            samesite="lax",
            path="/",
            max_age=settings.SESSION_TTL_MINUTES * 60,
        )

    request.state.current_user = user
    request.state.session_id = rotated_session
    request.state.session_db_id = session_obj.id
    return user


def require_roles(*allowed: UserRole) -> Callable[[User], User]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
