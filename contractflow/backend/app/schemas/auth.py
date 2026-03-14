"""Auth schemas."""
from __future__ import annotations

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import APIModel


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class UserResponse(APIModel):
    id: str
    email: str
    display_name: str
    role: UserRole
    department_id: str | None


class LoginResponse(APIModel):
    status: str
    user: UserResponse
