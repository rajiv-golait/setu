"""Patient memory (Current Truth). DEMO_MODE serves cached seed instantly."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Patient
from app.db.session import get_db
from app.deps import require_patient_access
from app.schemas.memory import CurrentTruthDTO
from app.services.memory.persistence import load_current_truth

router = APIRouter(prefix="/patients", tags=["memory"])


@router.get("/{patient_id}/memory", response_model=CurrentTruthDTO)
async def get_memory(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> CurrentTruthDTO:
    patient_id = settings.SEED_PATIENT_ID if settings.DEMO_MODE else patient.id
    return await load_current_truth(db, patient_id)
