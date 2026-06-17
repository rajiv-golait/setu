"""Admin provider management schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminProviderDTO(BaseModel):
    id: str
    supabase_user_id: str
    phone: str | None = None
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    verification_status: str = "pending"
    created_at: datetime


class AdminProviderGrant(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None


class AdminProviderPatch(BaseModel):
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    verification_status: str | None = None


class AdminVerifyRequest(BaseModel):
    status: str = "approved"  # approved|suspended|pending
