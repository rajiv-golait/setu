"""Patient Summary JSON (Marathi by default)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SummaryMedicine(BaseModel):
    name: str
    how_to_take: str
    plain: str


class PatientSummaryDTO(BaseModel):
    summary_id: str
    patient_id: str
    language: str = "mr"
    generated_at: datetime
    model: str
    greeting: str
    what_we_found: list[str] = []
    your_medicines: list[SummaryMedicine] = []
    what_to_watch: list[str] = []
    next_steps: list[str] = []
    disclaimer: str
