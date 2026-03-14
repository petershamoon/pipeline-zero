"""Notification worker logic."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.enums import ContractStatus


async def collect_expiring_contracts(db: AsyncSession, *, within_days: int = 14) -> list[Contract]:
    today = date.today()
    upper = today + timedelta(days=within_days)

    rows = (
        await db.execute(
            select(Contract).where(
                Contract.is_deleted.is_(False),
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date >= today,
                Contract.end_date <= upper,
            )
        )
    ).scalars().all()
    return rows
