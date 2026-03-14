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
