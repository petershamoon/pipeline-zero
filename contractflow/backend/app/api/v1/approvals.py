"""Approval templates and chain execution endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.approval_chain import ApprovalChain
from app.models.approval_step import ApprovalStep
from app.models.approval_template import ApprovalTemplate
from app.models.contract import Contract
from app.models.enums import ApprovalChainStatus, ApprovalDecision, AuditAction, ContractStatus
from app.models.user import User
from app.schemas.approvals import (
    ApprovalChainListResponse,
    ApprovalChainResponse,
    ApprovalDecisionRequest,
    ApprovalStepResponse,
    CreateApprovalChainRequest,
)
from app.services.audit import write_audit_event
from app.services.policy import can_approve, can_edit_contract, is_admin

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _chain_to_response(chain: ApprovalChain, steps: list[ApprovalStep]) -> ApprovalChainResponse:
    return ApprovalChainResponse(
        id=str(chain.id),
        contract_id=str(chain.contract_id),
        template_id=str(chain.template_id),
        status=chain.status,
        steps=[
            ApprovalStepResponse(
                id=str(step.id),
                chain_id=str(step.chain_id),
                step_order=step.step_order,
                approver_id=str(step.approver_id) if step.approver_id else None,
                decision=step.decision,
                decided_at=step.decided_at,
                comment=step.comment,
            )
            for step in sorted(steps, key=lambda item: item.step_order)
        ],
    )


@router.post("/chains", response_model=ApprovalChainResponse, status_code=status.HTTP_201_CREATED)
async def create_chain(
    payload: CreateApprovalChainRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalChainResponse:
    contract_id = uuid.UUID(payload.contract_id)
    template_id = uuid.UUID(payload.template_id)

    contract = (
        await db.execute(
            select(Contract).where(and_(Contract.id == contract_id, Contract.is_deleted.is_(False))).limit(1)
        )
    ).scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if not can_edit_contract(user, contract):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    template = (
        await db.execute(
            select(ApprovalTemplate).where(ApprovalTemplate.id == template_id, ApprovalTemplate.is_active.is_(True)).limit(1)
        )
    ).scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    chain = ApprovalChain(contract_id=contract.id, template_id=template.id, status=ApprovalChainStatus.PENDING)
    db.add(chain)
    await db.flush()

    steps: list[ApprovalStep] = []
    for index, raw_step in enumerate(template.steps_config):
        approver_id = raw_step.get("approver_id")
        step = ApprovalStep(
            chain_id=chain.id,
            step_order=int(raw_step.get("step_order", index + 1)),
            approver_id=uuid.UUID(approver_id) if approver_id else None,
            decision=ApprovalDecision.PENDING,
        )
        steps.append(step)
        db.add(step)

    contract.status = ContractStatus.PENDING_APPROVAL
    contract.version += 1
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.CREATE,
        resource_type="approval_chain",
        resource_id=chain.id,
        actor_id=user.id,
        contract_id=contract.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
        metadata_json={"template_id": str(template.id), "steps": len(steps)},
    )

    return _chain_to_response(chain, steps)


@router.get("/chains", response_model=ApprovalChainListResponse)
async def list_chains(
    contract_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalChainListResponse:
    query = select(ApprovalChain)
    if contract_id:
        query = query.where(ApprovalChain.contract_id == contract_id)
    chains = (await db.execute(query.order_by(ApprovalChain.created_at.desc()))).scalars().all()

    items: list[ApprovalChainResponse] = []
    for chain in chains:
        contract = (
            await db.execute(select(Contract).where(Contract.id == chain.contract_id).limit(1))
        ).scalar_one_or_none()
        if contract is None:
            continue
        if not is_admin(user) and user.id != contract.owner_id and user.department_id != contract.department_id:
            continue

        steps = (
            await db.execute(select(ApprovalStep).where(ApprovalStep.chain_id == chain.id))
        ).scalars().all()
        items.append(_chain_to_response(chain, steps))

    return ApprovalChainListResponse(items=items, total=len(items))


@router.post("/chains/{chain_id}/decision", response_model=ApprovalChainResponse)
async def submit_decision(
    chain_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApprovalChainResponse:
    if not can_approve(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approver role required")
    if payload.decision == ApprovalDecision.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be approved or rejected")

    chain = (
        await db.execute(select(ApprovalChain).where(ApprovalChain.id == chain_id).limit(1))
    ).scalar_one_or_none()
    if chain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval chain not found")
    if chain.status != ApprovalChainStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chain is not pending")

    steps = (
        await db.execute(select(ApprovalStep).where(ApprovalStep.chain_id == chain.id).order_by(ApprovalStep.step_order.asc()))
    ).scalars().all()

    pending_step = next((step for step in steps if step.decision == ApprovalDecision.PENDING), None)
    if pending_step is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending steps")

    if pending_step.approver_id and pending_step.approver_id != user.id and not is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This step is assigned to a different approver")

    pending_step.decision = payload.decision
    pending_step.comment = payload.comment
    pending_step.decided_at = datetime.now(timezone.utc)

    contract = (
        await db.execute(select(Contract).where(Contract.id == chain.contract_id).limit(1))
    ).scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    if payload.decision == ApprovalDecision.REJECTED:
        chain.status = ApprovalChainStatus.REJECTED
        contract.status = ContractStatus.DRAFT
    else:
        all_done = all(
            step.decision in {ApprovalDecision.APPROVED, ApprovalDecision.REJECTED}
            for step in steps
        )
        if all_done and all(step.decision == ApprovalDecision.APPROVED for step in steps):
            chain.status = ApprovalChainStatus.APPROVED
            contract.status = ContractStatus.ACTIVE

    contract.version += 1
    await db.flush()

    await write_audit_event(
        db,
        action=AuditAction.APPROVE if payload.decision == ApprovalDecision.APPROVED else AuditAction.REJECT,
        resource_type="approval_chain",
        resource_id=chain.id,
        actor_id=user.id,
        contract_id=chain.contract_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("X-Correlation-ID"),
        metadata_json={
            "step_order": pending_step.step_order,
            "decision": payload.decision.value,
        },
    )

    fresh_steps = (
        await db.execute(select(ApprovalStep).where(ApprovalStep.chain_id == chain.id).order_by(ApprovalStep.step_order.asc()))
    ).scalars().all()
    return _chain_to_response(chain, fresh_steps)
