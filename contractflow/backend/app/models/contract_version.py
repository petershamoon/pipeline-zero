"""Contract version (file upload) model."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ContractVersion(BaseModel):
    __tablename__ = "contract_versions"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    blob_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_contract_versions_contract_id", "contract_id"),
        Index(
            "uq_contract_version_number",
            "contract_id",
            "version_number",
            unique=True,
        ),
    )
