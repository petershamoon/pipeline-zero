"""Contract file upload and version endpoints."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_app_settings, get_current_user
from app.core.config import Settings
from app.core.database import get_db_session
from app.models.contract import Contract
from app.models.contract_version import ContractVersion
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.versions import ContractVersionListResponse, ContractVersionResponse, DownloadUrlResponse
from app.services.audit import write_audit_event
from app.services.policy import can_edit_contract, can_view_contract

router = APIRouter(prefix="/contracts/{contract_id}/versions", tags=["versions"])

MAX_MIME_BYTES = 2048
ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/png",
    "image/jpeg",
}


try:
    import magic  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    magic = None


def _uploads_root() -> Path:
    root = Path("/tmp/contractflow-uploads")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _guess_mime(data: bytes, file_hint: str | None) -> str:
    if magic is not None:
        detected = magic.from_buffer(data[:MAX_MIME_BYTES], mime=True)
        if detected:
            return str(detected)

    # Lightweight fallback by signature/content type hint.
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"PK"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return file_hint or "application/octet-stream"


def _to_response(version: ContractVersion) -> ContractVersionResponse:
    return ContractVersionResponse(
        id=str(version.id),
        contract_id=str(version.contract_id),
        version_number=version.version_number,
        file_name=version.file_name,
        file_size_bytes=version.file_size_bytes,
        mime_type=version.mime_type,
        sha256_checksum=version.sha256_checksum,
        blob_path=version.blob_path,
        uploaded_by_id=str(version.uploaded_by_id),
        created_at=version.created_at,
    )


def _sign_download(*, secret: str, version_id: uuid.UUID, exp: int) -> str:
    payload = f"{version_id}:{exp}".encode()
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")


async def _get_contract_or_404(db: AsyncSession, contract_id: uuid.UUID) -> Contract:
    contract = (
        await db.execute(
            select(Contract).where(and_(Contract.id == contract_id, Contract.is_deleted.is_(False))).limit(1)
        )
    ).scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return contract


async def _get_version_or_404(db: AsyncSession, contract_id: uuid.UUID, version_id: uuid.UUID) -> ContractVersion:
    version = (
        await db.execute(
            select(ContractVersion)
            .where(and_(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id))
            .limit(1)
        )
    ).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return version


@router.post("", response_model=ContractVersionResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract_version(
    contract_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> ContractVersionResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_edit_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    content = await file.read()
    size_limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > size_limit:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds size limit")

    detected_mime = _guess_mime(content, file.content_type)
    if detected_mime not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    checksum = hashlib.sha256(content).hexdigest()

    latest_version = (
        await db.execute(
            select(func.max(ContractVersion.version_number)).where(ContractVersion.contract_id == contract_id)
        )
    ).scalar_one()
    next_version = (latest_version or 0) + 1

    safe_filename = os.path.basename(file.filename or "upload.bin")
    blob_path = f"contracts/{contract_id}/v{next_version}/{safe_filename}"
    disk_path = _uploads_root() / blob_path
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    disk_path.write_bytes(content)

    version = ContractVersion(
        contract_id=contract_id,
        version_number=next_version,
        file_name=safe_filename,
        file_size_bytes=len(content),
        mime_type=detected_mime,
        sha256_checksum=checksum,
        blob_path=str(disk_path),
        uploaded_by_id=user.id,
    )
    db.add(version)
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.UPLOAD,
        resource_type="contract_version",
        resource_id=version.id,
        actor_id=user.id,
        contract_id=contract_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
        metadata_json={
            "file_name": safe_filename,
            "size": len(content),
            "mime_type": detected_mime,
            "sha256": checksum,
        },
    )

    return _to_response(version)


@router.get("", response_model=ContractVersionListResponse)
async def list_contract_versions(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ContractVersionListResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_view_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    versions = (
        await db.execute(
            select(ContractVersion)
            .where(ContractVersion.contract_id == contract_id)
            .order_by(ContractVersion.version_number.desc())
        )
    ).scalars().all()

    return ContractVersionListResponse(items=[_to_response(v) for v in versions], total=len(versions))


@router.get("/{version_id}/download", response_model=DownloadUrlResponse)
async def get_download_url(
    contract_id: uuid.UUID,
    version_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> DownloadUrlResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_view_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    version = await _get_version_or_404(db, contract_id, version_id)

    expires_in = settings.SAS_URL_TTL_MINUTES * 60
    exp = int(time.time()) + expires_in
    sig = quote(_sign_download(secret=settings.CSRF_SECRET, version_id=version.id, exp=exp))
    url = f"/api/v1/contracts/{contract_id}/versions/{version.id}/file?exp={exp}&sig={sig}"
    return DownloadUrlResponse(download_url=url, expires_in_seconds=expires_in)


@router.get("/{version_id}/file")
async def download_file(
    contract_id: uuid.UUID,
    version_id: uuid.UUID,
    exp: int = Query(...),
    sig: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> FileResponse:
    contract = await _get_contract_or_404(db, contract_id)
    if not can_view_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if int(time.time()) > exp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Download URL expired")

    version = await _get_version_or_404(db, contract_id, version_id)
    expected_sig = _sign_download(secret=settings.CSRF_SECRET, version_id=version.id, exp=exp)
    if not hmac.compare_digest(expected_sig, sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    path = Path(version.blob_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing")

    return FileResponse(path=path, filename=version.file_name, media_type=version.mime_type)
