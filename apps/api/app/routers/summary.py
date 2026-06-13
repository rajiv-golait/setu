"""Patient Summary route (Marathi by default). Lazy-generates if absent."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.errors import NOT_FOUND, AppError, not_found
from app.schemas.summary import PatientSummaryDTO
from app.services import persistence
from app.services.memory.persistence import load_current_truth
from app.services.reasoning.factory import get_reasoner
from app.services.summary import build_summary

router = APIRouter(prefix="/patients", tags=["summary"])


@router.get("/{patient_id}/summary", response_model=PatientSummaryDTO)
async def get_summary(
    patient_id: str,
    lang: str = Query(default="mr"),
    db: AsyncSession = Depends(get_db),
) -> PatientSummaryDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)

    cached = await persistence.latest_summary(db, patient_id, lang)
    if cached is not None:
        return cached

    # Lazy-generate from current truth + latest brief.
    truth = await load_current_truth(db, patient_id)
    brief = await persistence.latest_brief(db, patient_id)
    if brief is None:
        raise AppError(NOT_FOUND, "Generate a brief before a summary", details={"patient_id": patient_id}, retryable=False)
    summary = await build_summary(patient_id, truth, brief, get_reasoner(), lang=lang)
    await persistence.persist_summary(db, summary)
    await db.commit()
    return summary
