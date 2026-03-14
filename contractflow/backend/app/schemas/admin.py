"""Admin schemas."""
from __future__ import annotations

from pydantic import Field

from app.models.enums import UserRole
from app.schemas.common import APIModel


class DepartmentRequest(APIModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class DepartmentResponse(APIModel):
    id: str
    name: str
    description: str | None
    is_active: bool


class UserRequest(APIModel):
    email: str
    display_name: str
    role: UserRole
    department_id: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)


class UserResponse(APIModel):
    id: str
    email: str
    display_name: str
    role: UserRole
    department_id: str | None
    is_active: bool


class ApprovalTemplateRequest(APIModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    steps_config: list[dict]
    min_approvers: int = Field(default=1, ge=1)


class ApprovalTemplateResponse(APIModel):
    id: str
    name: str
    description: str | None
    steps_config: list[dict]
    min_approvers: int
    is_active: bool
