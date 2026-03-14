"""Approval schemas."""
from __future__ import annotations

from datetime import datetime

from app.models.enums import ApprovalChainStatus, ApprovalDecision
from app.schemas.common import APIModel


class CreateApprovalChainRequest(APIModel):
    contract_id: str
    template_id: str


class ApprovalDecisionRequest(APIModel):
    decision: ApprovalDecision
    comment: str | None = None


class ApprovalStepResponse(APIModel):
    id: str
    chain_id: str
    step_order: int
    approver_id: str | None
    decision: ApprovalDecision
    decided_at: datetime | None
    comment: str | None


class ApprovalChainResponse(APIModel):
    id: str
    contract_id: str
    template_id: str
    status: ApprovalChainStatus
    steps: list[ApprovalStepResponse]


class ApprovalChainListResponse(APIModel):
    items: list[ApprovalChainResponse]
    total: int
