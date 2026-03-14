"""Administrative APIs."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import require_roles
from app.core.database import get_db_session
from app.models.approval_template import ApprovalTemplate
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.admin import (
    ApprovalTemplateRequest,
    ApprovalTemplateResponse,
    DepartmentRequest,
    DepartmentResponse,
    UserRequest,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db_session)) -> list[DepartmentResponse]:
    rows = (await db.execute(select(Department).order_by(Department.name.asc()))).scalars().all()
    return [
        DepartmentResponse(id=str(dep.id), name=dep.name, description=dep.description, is_active=dep.is_active)
        for dep in rows
    ]


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DepartmentResponse:
    dep = Department(name=payload.name, description=payload.description, is_active=True)
    db.add(dep)
    await db.flush()
    return DepartmentResponse(id=str(dep.id), name=dep.name, description=dep.description, is_active=dep.is_active)


@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db_session)) -> list[UserResponse]:
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            department_id=str(user.department_id) if user.department_id else None,
            is_active=user.is_active,
        )
        for user in users
    ]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserRequest, db: AsyncSession = Depends(get_db_session)) -> UserResponse:
    department_id = uuid.UUID(payload.department_id) if payload.department_id else None
    user = User(
        email=payload.email,
        display_name=payload.display_name,
        role=payload.role,
        department_id=department_id,
        password_hash=auth_service.hash_password(payload.password) if payload.password else None,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=str(user.department_id) if user.department_id else None,
        is_active=user.is_active,
    )


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)) -> UserResponse:
    user = (await db.execute(select(User).where(User.id == user_id).limit(1))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await db.flush()
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=str(user.department_id) if user.department_id else None,
        is_active=user.is_active,
    )


@router.get("/templates", response_model=list[ApprovalTemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db_session)) -> list[ApprovalTemplateResponse]:
    templates = (await db.execute(select(ApprovalTemplate).order_by(ApprovalTemplate.name.asc()))).scalars().all()
    return [
        ApprovalTemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            steps_config=t.steps_config,
            min_approvers=t.min_approvers,
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.post("/templates", response_model=ApprovalTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: ApprovalTemplateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalTemplateResponse:
    if not payload.steps_config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template requires at least one step")

    template = ApprovalTemplate(
        name=payload.name,
        description=payload.description,
        steps_config=payload.steps_config,
        min_approvers=payload.min_approvers,
        is_active=True,
    )
    db.add(template)
    await db.flush()

    return ApprovalTemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        steps_config=template.steps_config,
        min_approvers=template.min_approvers,
        is_active=template.is_active,
    )
