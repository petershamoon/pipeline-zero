"""Audit query endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import require_roles
from app.core.database import get_db_session
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, UserRole
from app.schemas.audit import AuditEventListResponse, AuditEventResponse

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))],
)


@router.get("", response_model=AuditEventListResponse)
async def list_audit_events(
    contract_id: uuid.UUID | None = Query(default=None),
    actor_id: uuid.UUID | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
) -> AuditEventListResponse:
    clauses = []
    if contract_id:
        clauses.append(AuditLog.contract_id == contract_id)
    if actor_id:
        clauses.append(AuditLog.actor_id == actor_id)
    if action:
        clauses.append(AuditLog.action == action)

    query = select(AuditLog)
    if clauses:
        query = query.where(and_(*clauses))

    rows = (
        await db.execute(query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit))
    ).scalars().all()

    return AuditEventListResponse(
        items=[
            AuditEventResponse(
                id=str(row.id),
                actor_id=str(row.actor_id) if row.actor_id else None,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=str(row.resource_id),
                contract_id=str(row.contract_id) if row.contract_id else None,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                correlation_id=row.correlation_id,
                metadata_json=row.metadata_json,
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=len(rows),
    )
