"""Patient memory (Current Truth)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import get_auth_user_id, get_user_role, require_patient_or_provider_access
from app.schemas.memory import CurrentTruthDTO
from app.services.audit_phi import audit_phi_read
from app.services.memory.persistence import load_current_truth

router = APIRouter(prefix="/patients", tags=["memory"])


@router.get("/{patient_id}/memory", response_model=CurrentTruthDTO)
async def get_memory(
    request: Request,
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
) -> CurrentTruthDTO:
    patient_id = patient.id
    await audit_phi_read(
        db,
        patient_id=patient.id,
        resource="memory",
        actor_id=auth_user_id,
        actor_role=role,
        request=request,
    )
    await db.commit()
    return await load_current_truth(db, patient_id)
