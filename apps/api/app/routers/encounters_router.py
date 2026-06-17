"""Encounter, clinical notes, and prescription routes."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ClinicalNote, Encounter, Patient, Prescription, Provider
from app.db.session import get_db
from app.deps import (
    get_auth_user_id,
    get_user_role,
    require_approved_provider,
    require_provider_patient_access,
)
from app.errors import FORBIDDEN, AppError, not_found
from app.services import encounters as enc_svc
from app.services import notifications as notify_svc
from app.services.reasoning.factory import get_reasoner

router = APIRouter(prefix="/encounters", tags=["encounters"])


class NoteCreate(BaseModel):
    note_type: str
    body: str
    is_draft: bool = False


class PrescriptionCreate(BaseModel):
    items: list[dict]
    valid_until: datetime | None = None


class EncounterDTO(BaseModel):
    id: str
    patient_id: str
    provider_id: str
    appointment_id: str | None
    status: str
    encounter_type: str
    consult_room: str | None = None


class EncounterSummaryDTO(BaseModel):
    encounter_id: str
    appointment_id: str | None
    status: str
    notes: list[dict]
    prescriptions: list[dict]
    disclaimer: str = "Prepared summary for your records — not a diagnosis."


async def _build_summary(db: AsyncSession, enc: Encounter) -> EncounterSummaryDTO:
    notes = (
        await db.execute(
            select(ClinicalNote)
            .where(ClinicalNote.encounter_id == enc.id, ClinicalNote.is_draft.is_(False))
            .order_by(ClinicalNote.created_at)
        )
    ).scalars().all()
    rx_rows = (
        await db.execute(
            select(Prescription).where(Prescription.encounter_id == enc.id).order_by(Prescription.issued_at)
        )
    ).scalars().all()
    return EncounterSummaryDTO(
        encounter_id=enc.id,
        appointment_id=enc.appointment_id,
        status=enc.status,
        notes=[{"note_type": n.note_type, "body": n.body, "at": n.created_at.isoformat()} for n in notes],
        prescriptions=[
            {"id": r.id, "items": r.items, "issued_at": r.issued_at.isoformat()} for r in rx_rows
        ],
    )


@router.get("/{encounter_id}/prescriptions")
async def list_prescriptions(
    encounter_id: str,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    rows = (
        await db.execute(select(Prescription).where(Prescription.encounter_id == encounter_id))
    ).scalars().all()
    return [{"id": r.id, "items": r.items, "issued_at": r.issued_at.isoformat()} for r in rows]


@router.get("/{encounter_id}/summary", response_model=EncounterSummaryDTO)
async def encounter_summary(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
) -> EncounterSummaryDTO:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None:
        raise not_found("Encounter", encounter_id)
    if role == "provider":
        provider = (
            await db.execute(select(Provider).where(Provider.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if provider is None or enc.provider_id != provider.id:
            raise AppError(FORBIDDEN, "Not your encounter", retryable=False)
    elif role == "patient":
        patient = (
            await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if patient is None or enc.patient_id != patient.id:
            raise AppError(FORBIDDEN, "Not your encounter", retryable=False)
    else:
        raise AppError(FORBIDDEN, "Not allowed", retryable=False)
    return await _build_summary(db, enc)


@router.get("/{encounter_id}", response_model=EncounterDTO)
async def get_encounter(
    encounter_id: str,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> EncounterDTO:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    consult_room = None
    if enc.appointment_id:
        from app.db.models import Appointment

        appt = (
            await db.execute(select(Appointment).where(Appointment.id == enc.appointment_id))
        ).scalar_one_or_none()
        if appt:
            consult_room = appt.consult_room
    return EncounterDTO(
        id=enc.id,
        patient_id=enc.patient_id,
        provider_id=enc.provider_id,
        appointment_id=enc.appointment_id,
        status=enc.status,
        encounter_type=enc.encounter_type,
        consult_room=consult_room,
    )


@router.post("/{encounter_id}/notes")
async def add_note(
    encounter_id: str,
    body: NoteCreate,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> dict:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    note = await enc_svc.add_note(
        db,
        encounter_id,
        author_id=provider.id,
        note_type=body.note_type,
        body=body.body,
        is_draft=body.is_draft,
    )
    await db.commit()
    return {"id": note.id}


@router.post("/{encounter_id}/prescriptions")
async def add_prescription(
    encounter_id: str,
    body: PrescriptionCreate,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> dict:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    rx = await enc_svc.add_prescription(
        db,
        encounter_id,
        patient_id=enc.patient_id,
        provider_id=provider.id,
        items=body.items,
        valid_until=body.valid_until,
    )
    await db.commit()
    return {"id": rx.id}


@router.post("/{encounter_id}/complete")
async def complete_encounter(
    encounter_id: str,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> dict:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    await enc_svc.complete_encounter(db, encounter_id)
    if enc.appointment_id:
        from app.db.models import Appointment
        from app.schemas.appointments import AppointmentStatus

        appt = (
            await db.execute(select(Appointment).where(Appointment.id == enc.appointment_id))
        ).scalar_one_or_none()
        if appt and appt.status in (
            AppointmentStatus.accepted.value,
            AppointmentStatus.confirmed.value,
        ):
            appt.status = AppointmentStatus.completed.value
        await notify_svc.notify_patient_in_app(
            db,
            patient_id=enc.patient_id,
            title="Consultation complete",
            body="Your visit summary is ready to view.",
            data={"encounter_id": enc.id, "appointment_id": enc.appointment_id},
        )
    await db.commit()
    return {"status": "completed"}


@router.post("/{encounter_id}/draft-summary")
async def draft_summary(
    encounter_id: str,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """AI-assisted encounter summary draft — provider must approve before saving."""
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None or enc.provider_id != provider.id:
        raise not_found("Encounter", encounter_id)
    from app.services.memory.persistence import load_current_truth

    truth = await load_current_truth(db, enc.patient_id)
    reasoner = get_reasoner()
    draft = await reasoner.generate_explanation(truth, "en", "encounter")
    note = await enc_svc.add_note(
        db,
        encounter_id,
        author_id=provider.id,
        note_type="assessment",
        body=draft,
        is_draft=True,
    )
    await db.commit()
    return {"draft_note_id": note.id, "body": draft}


@router.get("/patient/{patient_id}/list", response_model=list[EncounterDTO])
async def list_patient_encounters(
    patient: Patient = Depends(require_provider_patient_access),
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> list[EncounterDTO]:
    rows = (
        await db.execute(
            select(Encounter)
            .where(Encounter.patient_id == patient.id, Encounter.provider_id == provider.id)
            .order_by(Encounter.created_at.desc())
        )
    ).scalars().all()
    return [
        EncounterDTO(
            id=e.id,
            patient_id=e.patient_id,
            provider_id=e.provider_id,
            appointment_id=e.appointment_id,
            status=e.status,
            encounter_type=e.encounter_type,
        )
        for e in rows
    ]
