"""Patient Summary route (Marathi by default). Lazy-generates if absent."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import require_patient_access
from app.errors import NOT_FOUND, AppError
from app.schemas.summary import PatientSummaryDTO
from app.services import persistence
from app.services.memory.persistence import load_current_truth
from app.services.reasoning.factory import get_reasoner
from app.services.summary import build_summary

router = APIRouter(prefix="/patients", tags=["summary"])


@router.get("/{patient_id}/summary", response_model=PatientSummaryDTO)
async def get_summary(
    patient: Patient = Depends(require_patient_access),
    lang: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PatientSummaryDTO:
    lang = lang or patient.lang_pref or "mr"

    cached = await persistence.latest_summary(db, patient.id, lang)
    if cached is not None:
        return cached

    truth = await load_current_truth(db, patient.id)
    brief = await persistence.latest_brief(db, patient.id)
    if brief is None:
        raise AppError(
            NOT_FOUND, "Generate a brief before a summary", details={"patient_id": patient.id}, retryable=False
        )
    summary = await build_summary(patient.id, truth, brief, get_reasoner(), lang=lang)
    await persistence.persist_summary(db, summary)
    await db.commit()
    return summary
