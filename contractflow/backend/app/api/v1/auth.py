"""Authentication endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_app_settings, get_current_user
from app.core.config import Settings
from app.core.database import get_db_session
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services import auth as auth_service
from app.services.audit import write_audit_event
from app.services.rate_limit import rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> LoginResponse:
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local auth is disabled")

    client_ip = request.client.host if request.client else "unknown"
    rate_result = await rate_limiter.allow(f"login:{client_ip}", limit=10, window_seconds=60)
    if not rate_result.allowed:
        response.headers["Retry-After"] = str(rate_result.retry_after_seconds)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")

    try:
        user = await auth_service.authenticate_local(db, email=payload.email, password=payload.password)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    raw_session, raw_csrf = await auth_service.create_session(db, user=user, settings=settings)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_session,
        httponly=True,
        secure=settings.SESSION_SECURE_COOKIE or settings.is_production,
        samesite="lax",
        path="/",
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=raw_csrf,
        httponly=False,
        secure=settings.SESSION_SECURE_COOKIE or settings.is_production,
        samesite="lax",
        path="/",
        max_age=settings.SESSION_TTL_MINUTES * 60,
    )

    await write_audit_event(
        db,
        action=AuditAction.LOGIN,
        resource_type="user",
        resource_id=user.id,
        actor_id=user.id,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )

    return LoginResponse(
        status="ok",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            department_id=str(user.department_id) if user.department_id else None,
        ),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, str]:
    session_db_id = getattr(request.state, "session_db_id", None)
    if session_db_id:
        await auth_service.destroy_session_by_id(db, session_id=session_db_id)

    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")

    await write_audit_event(
        db,
        action=AuditAction.LOGOUT,
        resource_type="user",
        resource_id=user.id,
        actor_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=str(user.department_id) if user.department_id else None,
    )


@router.post("/bootstrap-admin", response_model=UserResponse)
async def bootstrap_admin(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> UserResponse:
    if settings.is_production:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not available in production")

    existing_admin_count = (
        await db.execute(select(func.count()).select_from(User).where(User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN])))
    ).scalar_one()
    if existing_admin_count > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin already exists")

    user = User(
        email=payload.email,
        display_name="Bootstrap Admin",
        role=UserRole.SUPER_ADMIN,
        password_hash=auth_service.hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=None,
    )


@router.post("/purge-expired-sessions")
async def purge_expired_sessions(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    deleted = await auth_service.purge_expired_sessions(db)
    return {
        "status": "ok",
        "deleted": str(deleted),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
