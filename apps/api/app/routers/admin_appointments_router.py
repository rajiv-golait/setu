"""Admin appointment listing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.appointments import AppointmentDTO
from app.services import appointments as svc

router = APIRouter(prefix="/admin/appointments", tags=["admin"])


@router.get("", response_model=list[AppointmentDTO])
async def list_all_appointments(
    status: str | None = Query(default=None),
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AppointmentDTO]:
    stmt = select(Appointment).order_by(Appointment.created_at.desc())
    if status:
        stmt = stmt.where(Appointment.status == status)
    rows = (await db.execute(stmt.limit(100))).scalars().all()
    return [
        AppointmentDTO(
            id=a.id,
            patient_id=a.patient_id,
            provider_id=a.provider_id,
            specialty=a.specialty,
            status=a.status,
            scheduled_for=a.scheduled_for,
            consult_room=a.consult_room,
            referral_id=a.referral_id,
            triage_id=a.triage_id,
            notes=a.notes,
            requested_at=a.requested_at,
            created_at=a.created_at,
            updated_at=a.updated_at,
            **(await svc.to_dto_fields(db, a)),
        )
        for a in rows
    ]
