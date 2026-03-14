"""Audit schemas."""
from __future__ import annotations

from datetime import datetime

from app.models.enums import AuditAction
from app.schemas.common import APIModel


class AuditEventResponse(APIModel):
    id: str
    actor_id: str | None
    action: AuditAction
    resource_type: str
    resource_id: str
    contract_id: str | None
    ip_address: str | None
    user_agent: str | None
    correlation_id: str | None
    metadata_json: dict | None
    created_at: datetime


class AuditEventListResponse(APIModel):
    items: list[AuditEventResponse]
    total: int
