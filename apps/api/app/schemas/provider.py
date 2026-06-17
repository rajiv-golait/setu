"""Provider DTOs."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProviderDTO(BaseModel):
    id: str
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    verification_status: str = "pending"
    experience_years: int | None = None
    languages: list[str] | None = None
    location: str | None = None
    consultation_fee: float | None = None
    bio: str | None = None
    created_at: datetime


class ProviderPublicDTO(BaseModel):
    id: str
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    experience_years: int | None = None
    languages: list[str] | None = None
    location: str | None = None
    consultation_fee: float | None = None
    bio: str | None = None


class ProviderRegisterRequest(BaseModel):
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None


class ProviderUpdateRequest(BaseModel):
    display_name: str | None = None
    specialty: str | None = None
    facility: str | None = None
    experience_years: int | None = None
    languages: list[str] | None = None
    location: str | None = None
    consultation_fee: float | None = None
    bio: str | None = None


class ProviderDashboardDTO(BaseModel):
    pending_requests: int
    today_appointments: int
    completed_this_week: int
    patient_count: int
    follow_ups_due: int


class CredentialUploadResponse(BaseModel):
    id: str
    doc_type: str
    status: str
