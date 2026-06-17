"""Provider DTOs (Phase 1 — role foundation)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProviderDTO(BaseModel):
    id: str
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    created_at: datetime


class ProviderUpdateRequest(BaseModel):
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
