"""Current Truth (patient memory) — derived output of the reducer."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

EntryType = Literal["medication", "lab_result", "diagnosis", "allergy", "vital"]
TruthState = Literal["confirmed", "needs_review", "conflict", "possibly_discontinued"]


class CurrentTruthEntry(BaseModel):
    """One resolved fact about a patient. Pure reducer output (no DB id required)."""

    entry_type: EntryType
    normalized_key: str
    value: dict[str, Any]  # resolved current value (+ history for labs)
    confidence: float
    state: TruthState = "confirmed"
    source_claim_ids: list[str] = []
    updated_at: datetime | None = None


class CurrentTruthDTO(BaseModel):
    patient_id: str
    entries: list[CurrentTruthEntry]
    generated_at: datetime
