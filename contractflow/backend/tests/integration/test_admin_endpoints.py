"""Integration tests for admin CRUD endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole

from .conftest import (
    auth_headers,
    create_authenticated_session,
    create_test_department,
    create_test_user,
    set_auth_cookies,
)


# ---------------------------------------------------------------------------
# Department CRUD
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestAdminDepartments:
    """GET/POST /api/v1/admin/departments"""

    async def test_list_departments(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can list all departments."""
        dept = await create_test_department(db_session, name="ListDept-Admin")
        admin = await create_test_user(
            db_session,
            email="admin-listdept@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/departments")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        # Verify our department is in the list
        names = [d["name"] for d in body]
        assert "ListDept-Admin" in names

    async def test_create_department(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can create a new department."""
        setup_dept = await create_test_department(db_session, name="SetupDept-CreateDept")
        admin = await create_test_user(
            db_session,
            email="admin-createdept@example.com",
            role=UserRole.ADMIN,
            department_id=setup_dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/departments",
            json={"name": "New Engineering Dept", "description": "For engineers"},
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "New Engineering Dept"
        assert body["description"] == "For engineers"
        assert body["is_active"] is True
        assert "id" in body


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestAdminUsers:
    """GET/POST /api/v1/admin/users"""

    async def test_list_users(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can list all users."""
        dept = await create_test_department(db_session, name="ListUsers-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-listusers@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1

    async def test_create_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can create a new user."""
        dept = await create_test_department(db_session, name="CreateUser-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-createuser@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "new-user@example.com",
                "display_name": "New User",
                "role": UserRole.CONTRIBUTOR.value,
                "department_id": str(dept.id),
                "password": "new-user-password-123",
            },
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new-user@example.com"
        assert body["display_name"] == "New User"
        assert body["role"] == UserRole.CONTRIBUTOR.value
        assert body["is_active"] is True

    async def test_create_user_without_password(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can create a user without a password (e.g., for Entra-only users)."""
        dept = await create_test_department(db_session, name="NoPwUser-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-nopwuser@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "entra-user@example.com",
                "display_name": "Entra User",
                "role": UserRole.VIEWER.value,
                "department_id": str(dept.id),
            },
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == UserRole.VIEWER.value


# ---------------------------------------------------------------------------
# Deactivate User
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestDeactivateUser:
    """POST /api/v1/admin/users/{user_id}/deactivate"""

    async def test_deactivate_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can deactivate an existing user."""
        dept = await create_test_department(db_session, name="Deactivate-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-deactivate@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        target = await create_test_user(
            db_session,
            email="target-deactivate@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            f"/api/v1/admin/users/{target.id}/deactivate",
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_active"] is False
        assert body["email"] == "target-deactivate@example.com"

    async def test_deactivate_nonexistent_user_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Deactivating a nonexistent user returns 404."""
        dept = await create_test_department(db_session, name="Deactivate404-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-deactivate404@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/admin/users/{fake_id}/deactivate",
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Template CRUD
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestAdminTemplates:
    """GET/POST /api/v1/admin/templates"""

    async def test_list_templates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can list approval templates."""
        dept = await create_test_department(db_session, name="ListTemplates-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-listtpl@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/templates")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    async def test_create_template(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Admin can create an approval template."""
        dept = await create_test_department(db_session, name="CreateTemplate-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-createtpl@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/templates",
            json={
                "name": "Standard Approval",
                "description": "Two-step approval flow",
                "steps_config": [
                    {"step": 1, "role": "approver", "min_approvals": 1},
                    {"step": 2, "role": "admin", "min_approvals": 1},
                ],
                "min_approvers": 2,
            },
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Standard Approval"
        assert body["min_approvers"] == 2
        assert len(body["steps_config"]) == 2
        assert body["is_active"] is True

    async def test_create_template_without_steps_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Creating a template with empty steps_config returns 400."""
        dept = await create_test_department(db_session, name="EmptySteps-Dept")
        admin = await create_test_user(
            db_session,
            email="admin-emptysteps@example.com",
            role=UserRole.ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/templates",
            json={
                "name": "Empty Template",
                "description": "Should fail",
                "steps_config": [],
                "min_approvers": 1,
            },
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Non-admin authorization
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestAdminAuthorizationDenied:
    """Non-admin users should get 403 on all admin endpoints."""

    async def test_contributor_cannot_list_departments(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Contributor gets 403 on GET /api/v1/admin/departments."""
        dept = await create_test_department(db_session, name="AuthDenied-Dept")
        contributor = await create_test_user(
            db_session,
            email="contrib-denied@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, contributor)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/departments")
        assert resp.status_code == 403

    async def test_viewer_cannot_create_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Viewer gets 403 on POST /api/v1/admin/users."""
        dept = await create_test_department(db_session, name="ViewerDenied-Dept")
        viewer = await create_test_user(
            db_session,
            email="viewer-denied@example.com",
            role=UserRole.VIEWER,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, viewer)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "someone@example.com",
                "display_name": "Someone",
                "role": UserRole.VIEWER.value,
            },
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 403

    async def test_approver_cannot_access_admin_templates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Approver gets 403 on GET /api/v1/admin/templates."""
        dept = await create_test_department(db_session, name="ApproverDenied-Dept")
        approver = await create_test_user(
            db_session,
            email="approver-denied@example.com",
            role=UserRole.APPROVER,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, approver)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/templates")
        assert resp.status_code == 403

    async def test_unauthenticated_cannot_access_admin(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated request to admin endpoints returns 401."""
        resp = await client.get("/api/v1/admin/departments")
        assert resp.status_code == 401

    async def test_super_admin_can_access_admin_endpoints(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """SUPER_ADMIN should have access to admin endpoints."""
        dept = await create_test_department(db_session, name="SuperAdmin-Dept")
        super_admin = await create_test_user(
            db_session,
            email="superadmin-access@example.com",
            role=UserRole.SUPER_ADMIN,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, super_admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        resp = await client.get("/api/v1/admin/departments")
        assert resp.status_code == 200

        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 200

        resp = await client.get("/api/v1/admin/templates")
        assert resp.status_code == 200
