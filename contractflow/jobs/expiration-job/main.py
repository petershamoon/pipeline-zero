"""Scheduled expiration job entrypoint."""
from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.database import async_session_factory  # noqa: E402
from app.workers.expiration import run_expiration_scan  # noqa: E402


async def _run() -> None:
    async with async_session_factory() as db:
        count = await run_expiration_scan(db)
        await db.commit()
        print(f"expiration-job processed={count}")


if __name__ == "__main__":
    asyncio.run(_run())
