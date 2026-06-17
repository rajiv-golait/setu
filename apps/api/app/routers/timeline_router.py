"""Patient health timeline."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, Document, Encounter, Patient, Prescription, Vital
from app.db.session import get_db
from app.deps import get_auth_user_id, get_user_role, require_patient_access
from app.services.audit_phi import audit_phi_read

router = APIRouter(prefix="/patients", tags=["timeline"])


class TimelineEvent(BaseModel):
    event_type: str
    title: str
    at: datetime
    meta: dict | None = None


@router.get("/{patient_id}/timeline", response_model=list[TimelineEvent])
async def patient_timeline(
    request: Request,
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
) -> list[TimelineEvent]:
    pid = patient.id
    events: list[TimelineEvent] = []

    for doc in (
        await db.execute(
            select(Document).where(Document.patient_id == pid).order_by(Document.uploaded_at.desc())
        )
    ).scalars().all():
        events.append(
            TimelineEvent(
                event_type="document",
                title=doc.doc_type or "Document",
                at=doc.uploaded_at,
                meta={"status": doc.status},
            )
        )

    for appt in (
        await db.execute(
            select(Appointment).where(Appointment.patient_id == pid).order_by(Appointment.created_at.desc())
        )
    ).scalars().all():
        events.append(
            TimelineEvent(
                event_type="appointment",
                title=f"{appt.specialty} — {appt.status}",
                at=appt.scheduled_for or appt.created_at,
                meta={"appointment_id": appt.id},
            )
        )

    for enc in (
        await db.execute(
            select(Encounter).where(Encounter.patient_id == pid).order_by(Encounter.created_at.desc())
        )
    ).scalars().all():
        events.append(
            TimelineEvent(
                event_type="encounter",
                title=f"Consultation ({enc.status})",
                at=enc.created_at,
                meta={"encounter_id": enc.id},
            )
        )

    for rx in (
        await db.execute(
            select(Prescription).where(Prescription.patient_id == pid).order_by(Prescription.issued_at.desc())
        )
    ).scalars().all():
        events.append(
            TimelineEvent(
                event_type="prescription",
                title="Prescription issued",
                at=rx.issued_at,
                meta={"prescription_id": rx.id},
            )
        )

    for v in (
        await db.execute(
            select(Vital).where(Vital.patient_id == pid).order_by(Vital.measured_at.desc())
        )
    ).scalars().all():
        events.append(
            TimelineEvent(
                event_type="vital",
                title=v.vital_type,
                at=v.measured_at,
                meta=v.value,
            )
        )

    events.sort(key=lambda e: e.at, reverse=True)
    await audit_phi_read(
        db,
        patient_id=pid,
        resource="timeline",
        actor_id=auth_user_id,
        actor_role=role,
        request=request,
    )
    await db.commit()
    return events
