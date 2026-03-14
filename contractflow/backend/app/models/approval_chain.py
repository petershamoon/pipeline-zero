"""Approval chain model."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import ApprovalChainStatus


class ApprovalChain(BaseModel):
    __tablename__ = "approval_chains"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id"),
        nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_templates.id"),
        nullable=False,
    )
    status: Mapped[ApprovalChainStatus] = mapped_column(
        default=ApprovalChainStatus.PENDING,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_approval_chains_contract_id", "contract_id"),
    )
