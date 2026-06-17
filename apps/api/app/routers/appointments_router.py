"""Appointment routes (Phase 6 F2) — role-aware booking + lifecycle.

POST   /appointments        patient books (or a provider initiates).
GET    /appointments        role-scoped list (?status= filter).
PATCH  /appointments/{id}   submit an action; services.appointments.transition()
                            validates it. Status is never written raw.

health_worker proxy booking is intentionally deferred to F4 — it is NOT stubbed
here so it cannot misbehave half-built.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient, Provider
from app.db.session import get_db
from app.deps import (
    _check_patient_access,
    get_auth_user_id,
    get_or_create_provider,
    get_user_role,
)
from app.errors import FORBIDDEN, AppError
from app.schemas.appointments import AppointmentCreate, AppointmentDTO, AppointmentPatch
from app.services import appointments as svc

router = APIRouter(tags=["appointments"])


async def _dto(db: AsyncSession, appt) -> AppointmentDTO:
    joined = await svc.to_dto_fields(db, appt)
    return AppointmentDTO(
        id=appt.id,
        patient_id=appt.patient_id,
        provider_id=appt.provider_id,
        specialty=appt.specialty,
        status=appt.status,
        scheduled_for=appt.scheduled_for,
        consult_room=appt.consult_room,
        referral_id=appt.referral_id,
        triage_id=appt.triage_id,
        notes=appt.notes,
        requested_at=appt.requested_at,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
        **joined,
    )


@router.post("/appointments", response_model=AppointmentDTO, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(get_user_role),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> AppointmentDTO:
    if role == "provider":
        provider = await get_or_create_provider(db, auth_user_id)
        appt = await svc.book(
            db,
            patient_id=body.patient_id,
            specialty=body.specialty,
            scheduled_for=body.scheduled_for,
            referral_id=body.referral_id,
            triage_id=body.triage_id,
            notes=body.notes,
            booked_by=provider.id,
            provider_id=provider.id,
        )
    elif role == "patient":
        # Patient self-booking: must own the target patient record.
        patient = await _check_patient_access(body.patient_id, db, auth_user_id)
        appt = await svc.book(
            db,
            patient_id=patient.id,
            specialty=body.specialty,
            scheduled_for=body.scheduled_for,
            referral_id=body.referral_id,
            triage_id=body.triage_id,
            notes=body.notes,
            booked_by=patient.id,
        )
    elif role == "health_worker":
        from app.deps import get_or_create_health_worker, require_worker_patient_link

        worker = await get_or_create_health_worker(db, auth_user_id)
        patient = await require_worker_patient_link(body.patient_id, db, worker)
        appt = await svc.book(
            db,
            patient_id=patient.id,
            specialty=body.specialty,
            scheduled_for=body.scheduled_for,
            referral_id=body.referral_id,
            triage_id=body.triage_id,
            notes=body.notes,
            booked_by=worker.id,
        )
    else:
        raise AppError(FORBIDDEN, f"Role {role!r} may not book appointments", retryable=False)
    return await _dto(db, appt)


@router.get("/appointments", response_model=list[AppointmentDTO])
async def list_appointments(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(get_user_role),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> list[AppointmentDTO]:
    provider: Provider | None = None
    actor_id = auth_user_id or ""
    if role == "provider":
        provider = await get_or_create_provider(db, auth_user_id)
    elif role == "patient":
        # Resolve the patient record id for ownership scoping.
        patient = await _resolve_patient(db, auth_user_id)
        actor_id = patient.id if patient else (auth_user_id or "")
    elif role == "health_worker":
        from app.deps import get_or_create_health_worker

        worker = await get_or_create_health_worker(db, auth_user_id)
        actor_id = worker.id
    rows = await svc.list_for_role(
        db, role=role, actor_id=actor_id, provider=provider, status=status
    )
    return [await _dto(db, a) for a in rows]


@router.patch("/appointments/{appointment_id}", response_model=AppointmentDTO)
async def patch_appointment(
    appointment_id: str,
    body: AppointmentPatch,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(get_user_role),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> AppointmentDTO:
    appt = await svc.get(db, appointment_id)

    provider: Provider | None = None
    is_owner = False
    if role == "provider":
        provider = await get_or_create_provider(db, auth_user_id)
    elif role == "patient":
        patient = await _resolve_patient(db, auth_user_id)
        is_owner = patient is not None and patient.id == appt.patient_id

    appt = await svc.transition(
        db, appt, body.action, actor_role=role, is_owner=is_owner, provider=provider
    )
    return await _dto(db, appt)


async def _resolve_patient(db: AsyncSession, auth_user_id: str | None) -> Patient | None:
    """Find the patient record for the caller. In legacy/demo mode there is no
    Supabase id; access is then governed by _check_patient_access on write paths.
    """
    from sqlalchemy import select

    from app.config import settings

    if settings.DEMO_MODE:
        return (
            await db.execute(select(Patient).where(Patient.id == settings.SEED_PATIENT_ID))
        ).scalar_one_or_none()
    if auth_user_id is None:
        return None
    return (
        await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
