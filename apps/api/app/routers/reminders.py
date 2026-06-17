"""Reminder schedule route (B6)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Patient
from app.db.session import get_db
from app.deps import require_patient_access
from app.schemas.reminders import ReminderItem, ReminderScheduleDTO
from app.services import persistence
from app.services.memory.persistence import load_current_truth
from app.services.reminders import build_reminders

router = APIRouter(prefix="/patients", tags=["reminders"])


@router.get("/{patient_id}/reminders", response_model=ReminderScheduleDTO)
async def get_reminders(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> ReminderScheduleDTO:
    patient_id = patient.id
    truth = await load_current_truth(db, patient_id)
    items = build_reminders(truth)
    await persistence.replace_reminders(db, patient_id, items)
    await db.commit()

    return ReminderScheduleDTO(
        patient_id=patient_id,
        reminders=[ReminderItem(**item) for item in items],
    )
