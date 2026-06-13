"""Doctor Brief JSON — the product."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FlagSeverity = Literal["info", "warning", "critical"]
FlagType = Literal["abnormal_lab", "needs_review", "missing_data", "conflict"]
Trend = Literal["up", "down", "stable"]


class BriefMedication(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    since: str | None = None
    source: str | None = None


class BriefLab(BaseModel):
    test: str
    value: float | str
    unit: str | None = None
    flag: str | None = None
    date: str | None = None
    trend: Trend | None = None
    previous: float | str | None = None


class BriefCondition(BaseModel):
    condition: str
    since: str | None = None
    source: str | None = None


class BriefAllergy(BaseModel):
    substance: str
    severity: str | None = None


class TimelineEvent(BaseModel):
    date: str
    event: str


class BriefFlag(BaseModel):
    severity: FlagSeverity
    text: str
    type: FlagType


class DoctorBriefDTO(BaseModel):
    brief_id: str
    patient_id: str
    generated_at: datetime
    model: str
    one_line: str
    chief_concern: str
    active_medications: list[BriefMedication] = []
    recent_labs: list[BriefLab] = []
    active_conditions: list[BriefCondition] = []
    allergies: list[BriefAllergy] = []
    timeline: list[TimelineEvent] = []
    flags: list[BriefFlag] = []
    suggested_questions: list[str] = []
    source_documents: list[str] = []
    confidence_notes: str | None = None
