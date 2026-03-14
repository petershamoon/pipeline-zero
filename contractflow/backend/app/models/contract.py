"""Contract model — core domain entity."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import ContractStatus


class Contract(BaseModel):
    __tablename__ = "contracts"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    contract_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[ContractStatus] = mapped_column(default=ContractStatus.DRAFT, nullable=False)

    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    value_usd: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    renewal_notice_days: Mapped[int] = mapped_column(default=30, nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Optimistic locking
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_contract_dates"),
        CheckConstraint("value_usd >= 0", name="ck_contract_value_positive"),
        CheckConstraint("renewal_notice_days >= 0", name="ck_contract_renewal_notice_positive"),
        Index("ix_contracts_status", "status"),
        Index("ix_contracts_owner_id", "owner_id"),
        Index("ix_contracts_department_id", "department_id"),
    )
