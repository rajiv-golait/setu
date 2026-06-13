"""Claims JSON — extraction output, validation/memory input."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ClaimType = Literal[
    "medication",
    "lab_result",
    "diagnosis",
    "allergy",
    "vital",
    "procedure",
    "advice",
]

# Required fields per claim type (used by validation.py).
REQUIRED_FIELDS: dict[str, list[str]] = {
    "medication": ["name", "dose", "dose_unit", "frequency"],
    "lab_result": ["test_name", "value", "unit"],
    "diagnosis": ["condition", "status"],
    "allergy": ["substance"],
    "vital": ["name", "value", "unit"],
    "procedure": ["name"],
    "advice": ["text"],
}


class Claim(BaseModel):
    claim_id: str
    type: ClaimType
    fields: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at: date | None = None
    needs_review: bool = False


class ClaimsJSON(BaseModel):
    document_id: str
    patient_id: str
    extracted_at: datetime
    provider: str
    document_type: str
    overall_confidence: float = Field(ge=0.0, le=1.0)
    claims: list[Claim]
