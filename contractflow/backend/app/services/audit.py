"""Audit logging service."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


async def write_audit_event(
    db: AsyncSession,
    *,
    action: AuditAction,
    resource_type: str,
    resource_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    contract_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    correlation_id: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        contract_id=contract_id,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id,
        metadata_json=metadata_json,
    )
    db.add(event)
    await db.flush()
    return event
