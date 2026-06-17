"""Admin analytics schemas (Phase 6 F6) — counts only, no PII."""
from __future__ import annotations

from pydantic import BaseModel


class LanguageCount(BaseModel):
    lang_pref: str
    count: int


class AnalyticsOverviewDTO(BaseModel):
    consultations_completed: int
    rural_patients: int
    total_patients: int
    languages: list[LanguageCount]
    referral_completion_rate: float
    high_priority_triage: int
    avg_consultation_minutes: float | None = None
