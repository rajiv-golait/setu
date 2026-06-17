"""Auth session DTOs."""
from __future__ import annotations

from pydantic import BaseModel


class AuthMeDTO(BaseModel):
    user_id: str
    role: str
    verification_status: str | None = None
    provider_id: str | None = None
    patient_id: str | None = None
    health_worker_id: str | None = None
