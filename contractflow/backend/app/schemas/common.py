"""Shared API schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorEnvelope(BaseModel):
    error: str
    detail: str
