"""FHIR gateway — export bundle for interoperability (ABDM-ready posture)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import require_patient_access
from app.errors import NOT_FOUND, AppError
from app.services import persistence
from app.services.fhir_export import brief_to_fhir_bundle
from app.services.memory.persistence import load_current_truth

router = APIRouter(prefix="/fhir", tags=["fhir"])


@router.get("/patients/{patient_id}/bundle")
async def patient_fhir_bundle(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    brief = await persistence.latest_brief(db, patient.id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief for FHIR export", retryable=False)
    truth = await load_current_truth(db, patient.id)
    return brief_to_fhir_bundle(
        brief,
        truth=truth,
        patient_display=patient.display_name or "Patient",
    )
