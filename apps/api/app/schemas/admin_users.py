"""Admin user role management."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

UserPortalRole = Literal["patient", "provider"]


class SetUserRoleRequest(BaseModel):
    phone: str = Field(..., min_length=10)
    role: UserPortalRole
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None


class SetUserRoleResponse(BaseModel):
    supabase_user_id: str
    phone: str
    role: UserPortalRole
    provider_id: str | None = None
