"""Doctor Brief routes. GET latest; POST regenerates from current truth.

DEMO_MODE: GET returns the cached seed brief instantly, no pipeline.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.errors import NOT_FOUND, AppError, not_found
from app.schemas.brief import DoctorBriefDTO
from app.services import persistence
from app.services.brief import build_brief
from app.services.memory.persistence import recompute_current_truth
from app.services.orchestrator import _source_documents
from app.services.reasoning.factory import get_reasoner

router = APIRouter(prefix="/patients", tags=["brief"])


async def _ensure_patient(db: AsyncSession, patient_id: str) -> Patient:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)
    return patient


@router.get("/{patient_id}/brief", response_model=DoctorBriefDTO)
async def get_brief(patient_id: str, db: AsyncSession = Depends(get_db)) -> DoctorBriefDTO:
    await _ensure_patient(db, patient_id)
    brief = await persistence.latest_brief(db, patient_id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief generated yet", details={"patient_id": patient_id}, retryable=False)
    return brief


@router.post("/{patient_id}/brief", response_model=DoctorBriefDTO, status_code=201)
async def regenerate_brief(patient_id: str, db: AsyncSession = Depends(get_db)) -> DoctorBriefDTO:
    await _ensure_patient(db, patient_id)
    truth = await recompute_current_truth(db, patient_id)
    reasoner = get_reasoner()
    source_docs = await _source_documents(db, patient_id)
    brief = await build_brief(patient_id, truth, reasoner, source_docs)
    await persistence.persist_brief(db, brief)
    await db.commit()
    return brief
