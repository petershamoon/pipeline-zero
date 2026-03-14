"""OpenTelemetry initialization hooks."""
from __future__ import annotations

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except Exception:  # pragma: no cover
    FastAPIInstrumentor = None


def instrument_fastapi(app) -> None:
    if FastAPIInstrumentor is None:
        return
    FastAPIInstrumentor.instrument_app(app)
