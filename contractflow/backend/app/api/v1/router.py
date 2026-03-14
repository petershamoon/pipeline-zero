"""V1 API router aggregator."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.contracts import router as contracts_router
from app.api.v1.versions import router as versions_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(contracts_router)
v1_router.include_router(versions_router)
v1_router.include_router(approvals_router)
v1_router.include_router(audit_router)
v1_router.include_router(admin_router)
