"""Health worker schemas (Phase 6 F4)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WorkerDTO(BaseModel):
    id: str
    display_name: str | None = None
    facility_name: str | None = None
    facility_type: str | None = None
    district: str | None = None
    created_at: datetime


class AssignedPatientDTO(BaseModel):
    id: str
    display_name: str | None = None
    lang_pref: str
    is_rural: bool = False
    assigned_at: datetime


class ProxyPatientCreate(BaseModel):
    display_name: str
    phone: str | None = None
    lang_pref: str = "mr"
    is_rural: bool = False
