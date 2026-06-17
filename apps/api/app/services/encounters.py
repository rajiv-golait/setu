"""Encounter lifecycle — created on appointment accept, notes + prescriptions."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Appointment,
    ClinicalNote,
    ConsultationSession,
    Encounter,
    Prescription,
    ProviderAccessGrant,
)
from app.ids import new_id


async def create_encounter_for_appointment(
    db: AsyncSession,
    appt: Appointment,
    provider_id: str,
) -> Encounter:
    existing = (
        await db.execute(select(Encounter).where(Encounter.appointment_id == appt.id))
    ).scalar_one_or_none()
    if existing:
        return existing

    enc = Encounter(
        id=new_id("enc"),
        patient_id=appt.patient_id,
        provider_id=provider_id,
        appointment_id=appt.id,
        encounter_type="tele",
        status="open",
    )
    db.add(enc)

    session = ConsultationSession(id=new_id("csn"), appointment_id=appt.id)
    db.add(session)

    grant = ProviderAccessGrant(
        id=new_id("pag"),
        provider_id=provider_id,
        patient_id=appt.patient_id,
        appointment_id=appt.id,
    )
    db.add(grant)
    await db.flush()
    return enc


async def record_video_join(
    db: AsyncSession,
    appointment_id: str,
    *,
    role: str,
) -> None:
    row = (
        await db.execute(
            select(ConsultationSession).where(ConsultationSession.appointment_id == appointment_id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = ConsultationSession(id=new_id("csn"), appointment_id=appointment_id)
        db.add(row)
    now = datetime.now(timezone.utc)
    if role == "patient":
        row.video_joined_patient_at = now
    elif role == "provider":
        row.video_joined_provider_at = now
    if row.started_at is None:
        row.started_at = now
    await db.flush()


async def add_note(
    db: AsyncSession,
    encounter_id: str,
    *,
    author_id: str,
    note_type: str,
    body: str,
    is_draft: bool = False,
) -> ClinicalNote:
    note = ClinicalNote(
        id=new_id("note"),
        encounter_id=encounter_id,
        author_id=author_id,
        note_type=note_type,
        body=body,
        is_draft=is_draft,
    )
    db.add(note)
    await db.flush()
    return note


async def add_prescription(
    db: AsyncSession,
    encounter_id: str,
    *,
    patient_id: str,
    provider_id: str,
    items: list,
    valid_until: datetime | None = None,
) -> Prescription:
    rx = Prescription(
        id=new_id("rx"),
        encounter_id=encounter_id,
        patient_id=patient_id,
        provider_id=provider_id,
        items={"medications": items},
        valid_until=valid_until,
    )
    db.add(rx)
    await db.flush()
    return rx


async def complete_encounter(db: AsyncSession, encounter_id: str) -> Encounter:
    enc = (
        await db.execute(select(Encounter).where(Encounter.id == encounter_id))
    ).scalar_one_or_none()
    if enc is None:
        raise ValueError("encounter not found")
    enc.status = "completed"
    enc.completed_at = datetime.now(timezone.utc)
    if enc.appointment_id:
        sess = (
            await db.execute(
                select(ConsultationSession).where(
                    ConsultationSession.appointment_id == enc.appointment_id
                )
            )
        ).scalar_one_or_none()
        if sess and sess.ended_at is None:
            sess.ended_at = enc.completed_at
    await db.flush()
    return enc
