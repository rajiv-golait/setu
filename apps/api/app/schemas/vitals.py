"""Vitals schemas (Phase 6 F5) — informational only."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VitalType(str, Enum):
    blood_pressure = "blood_pressure"
    blood_sugar = "blood_sugar"
    spo2 = "spo2"
    heart_rate = "heart_rate"


class VitalCreate(BaseModel):
    vital_type: VitalType
    value: dict[str, Any]
    unit: str
    measured_at: datetime | None = None
    source: str | None = None


class VitalDTO(BaseModel):
    id: str
    patient_id: str
    vital_type: str
    value: dict[str, Any]
    unit: str
    measured_at: datetime
    source: str
    created_at: datetime
    flag: str | None = None
    flag_message: str | None = None


class VitalsSummaryDTO(BaseModel):
    patient_id: str
    latest: dict[str, VitalDTO] = Field(default_factory=dict)
    trends: dict[str, str] = Field(default_factory=dict)
