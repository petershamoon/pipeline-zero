"""Integration tests for contract CRUD and lifecycle endpoints."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ContractStatus, UserRole

from .conftest import (
    auth_headers,
    create_authenticated_session,
    create_test_department,
    create_test_user,
    set_auth_cookies,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contract_payload(
    *,
    owner_id: str,
    department_id: str,
    title: str = "Test Contract",
    contract_number: str | None = None,
) -> dict:
    """Build a valid ContractCreateRequest payload."""
    return {
        "title": title,
        "description": "Integration test contract",
        "contract_number": contract_number or f"TEST-{uuid.uuid4().hex[:8].upper()}",
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
        "value_usd": "5000.00",
        "renewal_notice_days": 30,
        "owner_id": owner_id,
        "department_id": department_id,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
class TestCreateContract:
    """POST /api/v1/contracts"""

    async def test_create_contract_as_contributor(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A contributor can create a contract in their department."""
        dept = await create_test_department(db_session, name="Legal-Create")
        user = await create_test_user(
            db_session,
            email="create-contrib@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        payload = _contract_payload(owner_id=str(user.id), department_id=str(dept.id))
        resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Test Contract"
        assert body["status"] == ContractStatus.DRAFT.value
        assert body["owner_id"] == str(user.id)
        assert body["department_id"] == str(dept.id)
        assert body["version"] == 1

    async def test_create_contract_as_viewer_returns_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A viewer cannot create contracts."""
        dept = await create_test_department(db_session, name="Legal-ViewerCreate")
        viewer = await create_test_user(
            db_session,
            email="viewer-create@example.com",
            role=UserRole.VIEWER,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, viewer)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        payload = _contract_payload(owner_id=str(viewer.id), department_id=str(dept.id))
        resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 403

    async def test_create_contract_as_admin_for_any_department(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """An admin can create a contract in any department."""
        dept_a = await create_test_department(db_session, name="Dept-A-AdminCreate")
        dept_b = await create_test_department(db_session, name="Dept-B-AdminCreate")
        admin = await create_test_user(
            db_session,
            email="admin-create@example.com",
            role=UserRole.ADMIN,
            department_id=dept_a.id,
        )
        other_user = await create_test_user(
            db_session,
            email="other-owner@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept_b.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        payload = _contract_payload(
            owner_id=str(other_user.id),
            department_id=str(dept_b.id),
            title="Admin-Created Contract",
        )
        resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Admin-Created Contract"


@pytest.mark.integration
@pytest.mark.asyncio
class TestListContracts:
    """GET /api/v1/contracts"""

    async def test_list_contracts_returns_items(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Authenticated user can list contracts."""
        dept = await create_test_department(db_session, name="Legal-List")
        user = await create_test_user(
            db_session,
            email="list-user@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        # Create a contract first
        payload = _contract_payload(owner_id=str(user.id), department_id=str(dept.id))
        create_resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert create_resp.status_code == 201

        # Now list
        resp = await client.get("/api/v1/contracts")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] >= 1

    async def test_list_contracts_unauthenticated_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/api/v1/contracts")
        assert resp.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetContract:
    """GET /api/v1/contracts/{id}"""

    async def test_get_contract_by_id(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Get a specific contract by its UUID."""
        dept = await create_test_department(db_session, name="Legal-Get")
        user = await create_test_user(
            db_session,
            email="get-user@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        # Create
        payload = _contract_payload(owner_id=str(user.id), department_id=str(dept.id))
        create_resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert create_resp.status_code == 201
        contract_id = create_resp.json()["id"]

        # Fetch
        resp = await client.get(f"/api/v1/contracts/{contract_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == contract_id
        assert body["title"] == "Test Contract"

    async def test_get_nonexistent_contract_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Requesting a non-existent contract returns 404."""
        dept = await create_test_department(db_session, name="Legal-Get404")
        user = await create_test_user(
            db_session,
            email="get404-user@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/contracts/{fake_id}")
        assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestStatusTransition:
    """POST /api/v1/contracts/{id}/status"""

    async def test_valid_transition_draft_to_pending(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """DRAFT -> PENDING_APPROVAL is a valid transition."""
        dept = await create_test_department(db_session, name="Legal-Transition")
        user = await create_test_user(
            db_session,
            email="transition-user@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        # Create a draft contract
        payload = _contract_payload(owner_id=str(user.id), department_id=str(dept.id))
        create_resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert create_resp.status_code == 201
        contract_id = create_resp.json()["id"]

        # Transition to pending_approval
        resp = await client.post(
            f"/api/v1/contracts/{contract_id}/status",
            json={"status": ContractStatus.PENDING_APPROVAL.value},
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == ContractStatus.PENDING_APPROVAL.value
        assert body["version"] == 2  # version should increment

    async def test_invalid_transition_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """DRAFT -> ACTIVE is not a valid transition, should return 400."""
        dept = await create_test_department(db_session, name="Legal-BadTransition")
        user = await create_test_user(
            db_session,
            email="bad-transition@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, user)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        # Create a draft contract
        payload = _contract_payload(owner_id=str(user.id), department_id=str(dept.id))
        create_resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert create_resp.status_code == 201
        contract_id = create_resp.json()["id"]

        # Attempt invalid transition: draft -> active
        resp = await client.post(
            f"/api/v1/contracts/{contract_id}/status",
            json={"status": ContractStatus.ACTIVE.value},
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
class TestContractAuthorization:
    """Authorization checks for contract operations."""

    async def test_contributor_cannot_perform_admin_status_transitions_on_other_dept(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """A contributor cannot transition status on a contract from another department."""
        dept_a = await create_test_department(db_session, name="Dept-A-Auth")
        dept_b = await create_test_department(db_session, name="Dept-B-Auth")

        admin = await create_test_user(
            db_session,
            email="auth-admin@example.com",
            role=UserRole.ADMIN,
            department_id=dept_a.id,
        )

        contributor = await create_test_user(
            db_session,
            email="auth-contributor@example.com",
            role=UserRole.CONTRIBUTOR,
            department_id=dept_b.id,
        )

        # Admin creates a contract in dept_a
        admin_session, admin_csrf = await create_authenticated_session(db_session, admin)
        await db_session.commit()

        set_auth_cookies(client, admin_session, admin_csrf)
        payload = _contract_payload(
            owner_id=str(admin.id),
            department_id=str(dept_a.id),
            title="Admin-Owned Contract",
        )
        create_resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(admin_csrf),
        )
        assert create_resp.status_code == 201
        contract_id = create_resp.json()["id"]

        # Now switch to contributor in dept_b
        contrib_session, contrib_csrf = await create_authenticated_session(db_session, contributor)
        await db_session.commit()

        # Clear previous cookies and set contributor's
        client.cookies.clear()
        set_auth_cookies(client, contrib_session, contrib_csrf)

        # Contributor in dept_b tries to transition the contract in dept_a
        resp = await client.post(
            f"/api/v1/contracts/{contract_id}/status",
            json={"status": ContractStatus.PENDING_APPROVAL.value},
            headers=auth_headers(contrib_csrf),
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_create_contract(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Viewers should not be able to create contracts."""
        dept = await create_test_department(db_session, name="Dept-ViewerBlock")
        viewer = await create_test_user(
            db_session,
            email="viewer-block@example.com",
            role=UserRole.VIEWER,
            department_id=dept.id,
        )
        raw_session, raw_csrf = await create_authenticated_session(db_session, viewer)
        await db_session.commit()

        set_auth_cookies(client, raw_session, raw_csrf)

        payload = _contract_payload(owner_id=str(viewer.id), department_id=str(dept.id))
        resp = await client.post(
            "/api/v1/contracts",
            json=payload,
            headers=auth_headers(raw_csrf),
        )
        assert resp.status_code == 403
