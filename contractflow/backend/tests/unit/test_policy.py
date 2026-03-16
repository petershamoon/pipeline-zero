from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models.contract import Contract
from app.models.department import Department
from app.models.enums import ContractStatus, UserRole
from app.models.user import User
from app.services.policy import can_approve, can_edit_contract, can_view_contract


@pytest.mark.unit
def test_policy_allows_admin_for_all_contract_actions() -> None:
    department = Department(id=uuid.uuid4(), name="Legal")
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role=UserRole.ADMIN,
        department_id=department.id,
    )
    owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        display_name="Owner",
        role=UserRole.CONTRIBUTOR,
        department_id=department.id,
    )
    contract = Contract(
        title="Master Services Agreement",
        contract_number="MSA-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("1000.00"),
        renewal_notice_days=30,
        owner_id=owner.id,
        department_id=department.id,
    )

    assert can_view_contract(admin, contract)
    assert can_edit_contract(admin, contract)
    assert can_approve(admin)


@pytest.mark.unit
def test_policy_limits_contributor_to_owner_or_department_scope() -> None:
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    contributor = User(
        id=uuid.uuid4(),
        email="contrib@example.com",
        display_name="Contributor",
        role=UserRole.CONTRIBUTOR,
        department_id=legal.id,
    )

    own_contract = Contract(
        title="Own Contract",
        contract_number="OWN-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 1),
        value_usd=Decimal("250.00"),
        renewal_notice_days=15,
        owner_id=contributor.id,
        department_id=finance.id,
    )

    other_owner = uuid.uuid4()
    other_contract = Contract(
        title="Other Contract",
        contract_number="OTH-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 1),
        value_usd=Decimal("250.00"),
        renewal_notice_days=15,
        owner_id=other_owner,
        department_id=finance.id,
    )

    assert can_view_contract(contributor, own_contract)
    assert can_edit_contract(contributor, own_contract)
    assert not can_edit_contract(contributor, other_contract)


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_viewer_can_view_any_contract_in_any_department() -> None:
    """Viewers have universal read access regardless of department."""
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    viewer = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        display_name="Viewer",
        role=UserRole.VIEWER,
        department_id=legal.id,
    )

    # Contract in same department
    same_dept_contract = Contract(
        title="Legal NDA",
        contract_number="NDA-001",
        status=ContractStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("500.00"),
        renewal_notice_days=30,
        owner_id=uuid.uuid4(),
        department_id=legal.id,
    )

    # Contract in a completely different department
    cross_dept_contract = Contract(
        title="Finance Lease",
        contract_number="FIN-001",
        status=ContractStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("10000.00"),
        renewal_notice_days=60,
        owner_id=uuid.uuid4(),
        department_id=finance.id,
    )

    assert can_view_contract(viewer, same_dept_contract)
    assert can_view_contract(viewer, cross_dept_contract)


@pytest.mark.unit
def test_viewer_cannot_edit_any_contract() -> None:
    """Viewers must not be able to edit contracts, even in their own department."""
    dept = Department(id=uuid.uuid4(), name="Legal")

    viewer = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        display_name="Viewer",
        role=UserRole.VIEWER,
        department_id=dept.id,
    )

    contract = Contract(
        title="Read-Only Contract",
        contract_number="RO-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        value_usd=Decimal("100.00"),
        renewal_notice_days=15,
        owner_id=viewer.id,  # even if the viewer "owns" it
        department_id=dept.id,
    )

    assert not can_edit_contract(viewer, contract)
    assert not can_approve(viewer)


@pytest.mark.unit
def test_approver_can_view_and_approve() -> None:
    """Approvers can view contracts in their department and approve."""
    dept = Department(id=uuid.uuid4(), name="Legal")

    approver = User(
        id=uuid.uuid4(),
        email="approver@example.com",
        display_name="Approver",
        role=UserRole.APPROVER,
        department_id=dept.id,
    )

    contract = Contract(
        title="Approval Target",
        contract_number="APP-001",
        status=ContractStatus.PENDING_APPROVAL,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("5000.00"),
        renewal_notice_days=30,
        owner_id=uuid.uuid4(),  # owned by someone else
        department_id=dept.id,
    )

    assert can_view_contract(approver, contract)
    assert can_approve(approver)


@pytest.mark.unit
def test_approver_can_edit_in_own_department() -> None:
    """Approvers can edit contracts that belong to their department."""
    dept = Department(id=uuid.uuid4(), name="Legal")

    approver = User(
        id=uuid.uuid4(),
        email="approver@example.com",
        display_name="Approver",
        role=UserRole.APPROVER,
        department_id=dept.id,
    )

    same_dept = Contract(
        title="Dept Contract",
        contract_number="D-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("2000.00"),
        renewal_notice_days=30,
        owner_id=uuid.uuid4(),
        department_id=dept.id,
    )

    assert can_edit_contract(approver, same_dept)


@pytest.mark.unit
def test_approver_cannot_edit_other_department_contract() -> None:
    """Approvers cannot edit contracts outside their department that they don't own."""
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    approver = User(
        id=uuid.uuid4(),
        email="approver@example.com",
        display_name="Approver",
        role=UserRole.APPROVER,
        department_id=legal.id,
    )

    other_dept_contract = Contract(
        title="Finance Only",
        contract_number="FIN-002",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("8000.00"),
        renewal_notice_days=30,
        owner_id=uuid.uuid4(),
        department_id=finance.id,
    )

    assert not can_edit_contract(approver, other_dept_contract)


@pytest.mark.unit
def test_super_admin_has_full_access() -> None:
    """SUPER_ADMIN should have full access to view, edit, and approve any contract."""
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    super_admin = User(
        id=uuid.uuid4(),
        email="superadmin@example.com",
        display_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        department_id=legal.id,
    )

    # Contract in a different department, owned by someone else
    foreign_contract = Contract(
        title="Foreign Contract",
        contract_number="FOR-001",
        status=ContractStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        value_usd=Decimal("50000.00"),
        renewal_notice_days=90,
        owner_id=uuid.uuid4(),
        department_id=finance.id,
    )

    assert can_view_contract(super_admin, foreign_contract)
    assert can_edit_contract(super_admin, foreign_contract)
    assert can_approve(super_admin)


@pytest.mark.unit
def test_contributor_cannot_edit_cross_department_contract_they_dont_own() -> None:
    """A contributor must not edit a contract from another department they don't own."""
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    contributor = User(
        id=uuid.uuid4(),
        email="contrib@example.com",
        display_name="Contributor",
        role=UserRole.CONTRIBUTOR,
        department_id=legal.id,
    )

    cross_dept_contract = Contract(
        title="Cross Dept Contract",
        contract_number="CROSS-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        value_usd=Decimal("3000.00"),
        renewal_notice_days=15,
        owner_id=uuid.uuid4(),  # different owner
        department_id=finance.id,  # different department
    )

    assert not can_edit_contract(contributor, cross_dept_contract)


@pytest.mark.unit
def test_contributor_can_edit_own_contract_in_other_department() -> None:
    """A contributor CAN edit a contract they own, even if it is in another department."""
    legal = Department(id=uuid.uuid4(), name="Legal")
    finance = Department(id=uuid.uuid4(), name="Finance")

    contributor = User(
        id=uuid.uuid4(),
        email="contrib@example.com",
        display_name="Contributor",
        role=UserRole.CONTRIBUTOR,
        department_id=legal.id,
    )

    own_cross_dept = Contract(
        title="Owned Cross Dept",
        contract_number="OCROSS-001",
        status=ContractStatus.DRAFT,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        value_usd=Decimal("1500.00"),
        renewal_notice_days=15,
        owner_id=contributor.id,  # they own it
        department_id=finance.id,  # different department
    )

    assert can_edit_contract(contributor, own_cross_dept)


@pytest.mark.unit
def test_contributor_cannot_approve() -> None:
    """Contributors should not have approval permissions."""
    contributor = User(
        id=uuid.uuid4(),
        email="contrib@example.com",
        display_name="Contributor",
        role=UserRole.CONTRIBUTOR,
        department_id=uuid.uuid4(),
    )

    assert not can_approve(contributor)


@pytest.mark.unit
def test_viewer_cannot_approve() -> None:
    """Viewers should not have approval permissions."""
    viewer = User(
        id=uuid.uuid4(),
        email="viewer@example.com",
        display_name="Viewer",
        role=UserRole.VIEWER,
        department_id=uuid.uuid4(),
    )

    assert not can_approve(viewer)


@pytest.mark.unit
def test_admin_can_approve() -> None:
    """ADMIN role should have approval permissions."""
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role=UserRole.ADMIN,
        department_id=uuid.uuid4(),
    )

    assert can_approve(admin)
