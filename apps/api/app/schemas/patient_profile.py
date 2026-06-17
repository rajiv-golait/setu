"""Patient profile extension schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class PatientProfileDTO(BaseModel):
    patient_id: str
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    allergies_known: list[str] | None = None
    chronic_conditions: list[str] | None = None
    emergency_contact: dict | None = None
    district: str | None = None
    state: str | None = None
    updated_at: datetime | None = None


class PatientProfileUpdate(BaseModel):
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    allergies_known: list[str] | None = None
    chronic_conditions: list[str] | None = None
    emergency_contact: dict | None = None
    district: str | None = None
    state: str | None = None
