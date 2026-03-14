"""Contract CRUD and lifecycle endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.contract import Contract
from app.models.enums import AuditAction, ContractStatus, UserRole
from app.models.user import User
from app.schemas.contracts import (
    ContractCreateRequest,
    ContractListResponse,
    ContractResponse,
    ContractStatusUpdateRequest,
    ContractUpdateRequest,
)
from app.services.audit import write_audit_event
from app.services.policy import can_edit_contract, can_view_contract, is_admin

router = APIRouter(prefix="/contracts", tags=["contracts"])

ALLOWED_TRANSITIONS: dict[ContractStatus, set[ContractStatus]] = {
    ContractStatus.DRAFT: {ContractStatus.PENDING_APPROVAL, ContractStatus.ARCHIVED},
    ContractStatus.PENDING_APPROVAL: {ContractStatus.ACTIVE, ContractStatus.DRAFT, ContractStatus.ARCHIVED},
    ContractStatus.ACTIVE: {ContractStatus.EXPIRED, ContractStatus.TERMINATED, ContractStatus.ARCHIVED},
    ContractStatus.EXPIRED: {ContractStatus.ARCHIVED},
    ContractStatus.TERMINATED: {ContractStatus.ARCHIVED},
    ContractStatus.ARCHIVED: set(),
}


def _to_response(contract: Contract) -> ContractResponse:
    return ContractResponse(
        id=str(contract.id),
        title=contract.title,
        description=contract.description,
        contract_number=contract.contract_number,
        status=contract.status,
        start_date=contract.start_date,
        end_date=contract.end_date,
        value_usd=contract.value_usd,
        renewal_notice_days=contract.renewal_notice_days,
        owner_id=str(contract.owner_id),
        department_id=str(contract.department_id),
        is_deleted=contract.is_deleted,
        version=contract.version,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


async def _get_contract_or_404(db: AsyncSession, contract_id: uuid.UUID) -> Contract:
    contract = (
        await db.execute(
            select(Contract).where(and_(Contract.id == contract_id, Contract.is_deleted.is_(False))).limit(1)
        )
    ).scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractListResponse:
    query = select(Contract).where(Contract.is_deleted.is_(False))

    if user.role in {UserRole.CONTRIBUTOR, UserRole.APPROVER} and not is_admin(user):
        query = query.where(
            or_(
                Contract.owner_id == user.id,
                Contract.department_id == user.department_id,
            )
        )

    rows = (
        await db.execute(
            query.order_by(Contract.created_at.desc(), Contract.id.asc()).offset(skip).limit(limit)
        )
    ).scalars().all()

    return ContractListResponse(items=[_to_response(contract) for contract in rows], total=len(rows))


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    payload: ContractCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    if user.role not in {UserRole.CONTRIBUTOR, UserRole.APPROVER, UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    owner_id = uuid.UUID(payload.owner_id)
    department_id = uuid.UUID(payload.department_id)

    if not is_admin(user) and owner_id != user.id and user.department_id != department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create contract outside your scope")

    contract = Contract(
        title=payload.title,
        description=payload.description,
        contract_number=payload.contract_number,
        status=ContractStatus.DRAFT,
        start_date=payload.start_date,
        end_date=payload.end_date,
        value_usd=payload.value_usd,
        renewal_notice_days=payload.renewal_notice_days,
        owner_id=owner_id,
        department_id=department_id,
    )
    db.add(contract)
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.CREATE,
        resource_type="contract",
        resource_id=contract.id,
        actor_id=user.id,
        contract_id=contract.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )

    return _to_response(contract)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_view_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _to_response(contract)


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: uuid.UUID,
    payload: ContractUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_edit_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    changed_fields: dict[str, str] = {}
    for field_name, new_value in payload.model_dump(exclude_unset=True).items():
        setattr(contract, field_name, new_value)
        changed_fields[field_name] = str(new_value)

    contract.version += 1
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.UPDATE,
        resource_type="contract",
        resource_id=contract.id,
        actor_id=user.id,
        contract_id=contract.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
        metadata_json={"changed_fields": changed_fields},
    )

    return _to_response(contract)


@router.post("/{contract_id}/status", response_model=ContractResponse)
async def transition_contract_status(
    contract_id: uuid.UUID,
    payload: ContractStatusUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_edit_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    allowed_next = ALLOWED_TRANSITIONS[contract.status]
    if payload.status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {contract.status.value} -> {payload.status.value}",
        )

    previous = contract.status
    contract.status = payload.status
    contract.version += 1
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.STATUS_CHANGE,
        resource_type="contract",
        resource_id=contract.id,
        actor_id=user.id,
        contract_id=contract.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
        metadata_json={"previous_status": previous.value, "next_status": payload.status.value},
    )

    return _to_response(contract)


@router.post("/{contract_id}/archive", response_model=ContractResponse)
async def archive_contract(
    contract_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_edit_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    contract.is_deleted = True
    contract.status = ContractStatus.ARCHIVED
    contract.version += 1
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.DELETE,
        resource_type="contract",
        resource_id=contract.id,
        actor_id=user.id,
        contract_id=contract.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )

    return _to_response(contract)
