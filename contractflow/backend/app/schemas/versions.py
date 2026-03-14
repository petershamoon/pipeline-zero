"""Contract version schemas."""
from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class ContractVersionResponse(APIModel):
    id: str
    contract_id: str
    version_number: int
    file_name: str
    file_size_bytes: int
    mime_type: str
    sha256_checksum: str
    blob_path: str
    uploaded_by_id: str
    created_at: datetime


class ContractVersionListResponse(APIModel):
    items: list[ContractVersionResponse]
    total: int


class DownloadUrlResponse(APIModel):
    download_url: str
    expires_in_seconds: int
