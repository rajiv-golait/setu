"""Patient memory (Current Truth). DEMO_MODE serves cached seed instantly."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Patient
from app.db.session import get_db
from app.errors import not_found
from app.schemas.memory import CurrentTruthDTO
from app.services.memory.persistence import load_current_truth

router = APIRouter(prefix="/patients", tags=["memory"])


@router.get("/{patient_id}/memory", response_model=CurrentTruthDTO)
async def get_memory(patient_id: str, db: AsyncSession = Depends(get_db)) -> CurrentTruthDTO:
    # DEMO_MODE: serve the seeded patient's cached truth instantly, no pipeline.
    if settings.DEMO_MODE:
        patient_id = settings.SEED_PATIENT_ID

    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)

    # Reads persisted current_truth as-is (already instant — no recompute).
    return await load_current_truth(db, patient_id)
