"""Integration tests for authentication API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole

from .conftest import (
    auth_headers,
    create_authenticated_session,
    create_test_user,
    set_auth_cookies,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestBootstrapAdmin:
    """POST /api/v1/auth/bootstrap-admin"""

    async def test_bootstrap_creates_first_admin(self, client: AsyncClient) -> None:
        """When no admin exists, bootstrap-admin creates a SUPER_ADMIN user."""
        resp = await client.post(
            "/api/v1/auth/bootstrap-admin",
            json={"email": "admin@example.com", "password": "admin-password-123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "admin@example.com"
        assert body["role"] == UserRole.SUPER_ADMIN.value
        assert body["display_name"] == "Bootstrap Admin"

    async def test_bootstrap_fails_if_admin_already_exists(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """When an admin already exists, bootstrap returns 409 Conflict."""
        await create_test_user(
            db_session,
            email="existing-admin@example.com",
            role=UserRole.SUPER_ADMIN,
        )
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/bootstrap-admin",
            json={"email": "new-admin@example.com", "password": "admin-password-456"},
        )
        assert resp.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_with_valid_credentials(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Valid email + password returns 200 with user info and sets cookies."""
        password = "my-secret-pass-123"
        await create_test_user(
            db_session,
            email="login-user@example.com",
            password=password,
            role=UserRole.CONTRIBUTOR,
        )
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login-user@example.com", "password": password},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["user"]["email"] == "login-user@example.com"
        assert body["user"]["role"] == UserRole.CONTRIBUTOR.value

        # Session and CSRF cookies should be set
        assert "cf_session" in resp.cookies
        assert "cf_csrf" in resp.cookies

    async def test_login_with_wrong_password_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Wrong password returns 401."""
        await create_test_user(
            db_session,
            email="wrongpw@example.com",
            password="correct-password-123",
        )
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrong-password-123"},
        )
        assert resp.status_code == 401

    async def test_login_with_nonexistent_email_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Non-existent email returns 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "any-password-123"},
        )
        assert resp.status_code == 401

    async def test_login_with_inactive_user_returns_401(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Inactive user returns 401 even with correct password."""
        password = "active-pass-12345"
        await create_test_user(
            db_session,
            email="inactive@example.com",
            password=password,
            is_active=False,
        )
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": password},
        )
        assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestMe:
    """GET /api/v1/auth/me"""

    async def test_me_returns_current_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated user gets their own profile via /me."""
        user = await create_test_user(
            db_session,
            email="me-user@example.com",
            role=UserRole.APPROVER,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "me-user@example.com"
        assert body["role"] == UserRole.APPROVER.value

    async def test_me_without_session_returns_401(self, client: AsyncClient) -> None:
        """Unauthenticated request to /me returns 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestLogout:
    """POST /api/v1/auth/logout"""

    async def test_logout_clears_session(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Logout returns 200 and clears cookies."""
        user = await create_test_user(
            db_session,
            email="logout-user@example.com",
            role=UserRole.CONTRIBUTOR,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    async def test_logout_without_auth_returns_401(self, client: AsyncClient) -> None:
        """Logout without authentication returns 401."""
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
