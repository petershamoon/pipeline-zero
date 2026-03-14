"""Scheduled notification job entrypoint."""
from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.database import async_session_factory  # noqa: E402
from app.workers.notification import collect_expiring_contracts  # noqa: E402


async def _run() -> None:
    async with async_session_factory() as db:
        contracts = await collect_expiring_contracts(db, within_days=14)
        await db.commit()
        print(f"notification-job expiring_count={len(contracts)}")


if __name__ == "__main__":
    asyncio.run(_run())
