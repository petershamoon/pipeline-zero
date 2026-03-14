"""Unit tests for health endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.unit
class TestHealthEndpoints:
    async def test_liveness_returns_ok(self):
        """GET /health/live returns 200 with status ok."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    async def test_liveness_is_unauthenticated(self):
        """Health endpoints do not require auth."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
