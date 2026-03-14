"""Authorization policy helpers."""
from __future__ import annotations

from app.models.contract import Contract
from app.models.enums import UserRole
from app.models.user import User


def is_admin(user: User) -> bool:
    return user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}


def can_view_contract(user: User, contract: Contract) -> bool:
    if is_admin(user):
        return True
    if user.role == UserRole.VIEWER:
        return True
    return user.id == contract.owner_id or user.department_id == contract.department_id


def can_edit_contract(user: User, contract: Contract) -> bool:
    if is_admin(user):
        return True
    if user.role not in {UserRole.CONTRIBUTOR, UserRole.APPROVER}:
        return False
    return user.id == contract.owner_id or user.department_id == contract.department_id


def can_approve(user: User) -> bool:
    return is_admin(user) or user.role in {UserRole.APPROVER}
