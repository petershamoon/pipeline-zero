"""Contract domain schemas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.models.enums import ContractStatus
from app.schemas.common import APIModel


class ContractCreateRequest(APIModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    contract_number: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    value_usd: Decimal = Field(ge=0)
    renewal_notice_days: int = Field(default=30, ge=0)
    owner_id: str
    department_id: str


class ContractUpdateRequest(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    value_usd: Decimal | None = Field(default=None, ge=0)
    renewal_notice_days: int | None = Field(default=None, ge=0)


class ContractStatusUpdateRequest(APIModel):
    status: ContractStatus


class ContractResponse(APIModel):
    id: str
    title: str
    description: str | None
    contract_number: str
    status: ContractStatus
    start_date: date
    end_date: date
    value_usd: Decimal
    renewal_notice_days: int
    owner_id: str
    department_id: str
    is_deleted: bool
    version: int
    created_at: datetime
    updated_at: datetime


class ContractListResponse(APIModel):
    items: list[ContractResponse]
    total: int
