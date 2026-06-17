"""Export DTOs (FHIR + eSanjeevani framing)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EsanjeewaniExportDTO(BaseModel):
    patient_id: str
    brief_id: str
    text: str


class FhirExportDTO(BaseModel):
    patient_id: str
    brief_id: str
    bundle: dict[str, Any]
