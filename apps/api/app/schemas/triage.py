"""Triage DTOs (Phase 6 F1).

NON-DIAGNOSTIC care routing. The output is a priority band + a routing
recommendation, never a diagnosis, disease prediction, or medicine. The
deterministic engine decides priority/recommendation; the reasoner only
phrases `message` in the patient's language.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Computed deterministically — never by the model.
Priority = Literal["low", "medium", "high"]
Recommendation = Literal["visit_phc", "schedule_specialist", "emergency"]


class TriageRequest(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    age: int | None = None
    existing_conditions: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)


class TriageResultDTO(BaseModel):
    id: str
    patient_id: str
    priority: Priority
    recommendation: Recommendation
    # Deterministic, human-readable factors + matched rule ids (auditability).
    rationale: dict
    # Lang-aware phrasing of the fixed recommendation. NEVER overrides priority.
    message: str | None = None
    lang: str = "mr"
    engine_version: str
    created_at: datetime
    # Surfaced in the UI alongside every result. Non-negotiable framing.
    disclaimer: str = (
        "This is guidance on where to seek care, not a diagnosis. It does not "
        "identify any disease or recommend medicine. In an emergency, call local "
        "emergency services or go to the nearest hospital."
    )
