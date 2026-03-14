"""Contract expiration worker logic."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.enums import ContractStatus


async def run_expiration_scan(db: AsyncSession) -> int:
    today = date.today()
    rows = (
        await db.execute(
            select(Contract).where(
                Contract.is_deleted.is_(False),
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date < today,
            )
        )
    ).scalars().all()

    for contract in rows:
        contract.status = ContractStatus.EXPIRED
        contract.version += 1

    await db.flush()
    return len(rows)
