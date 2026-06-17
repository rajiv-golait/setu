"""Appointment service (Phase 6 F2).

All business rules live here so the router stays thin:
  * book()          — create a `requested` appointment.
  * transition()     — the ONLY way status changes; validated against
                       schemas.appointments.ALLOWED_TRANSITIONS (legal edge +
                       permitted role). Illegal edges / role mismatches raise.
  * list_for_role()  — role-scoped listing (patient: own; provider: assigned +
                       matching-specialty unassigned queue).

On `accept` the provider gets a deterministic Jitsi room (reusing
services/video.consult_room_name — no duplicate room logic) and an in-app
"Upcoming" reminder row is APPENDED via the existing Reminder table. There is no
push worker: the schedule surfaces in-app only, exactly like B6 reminders.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, Provider
from app.db.models import Reminder as ReminderRow
from app.errors import FORBIDDEN, VALIDATION_ERROR, AppError, not_found
from app.ids import new_id
from app.schemas.appointments import ALLOWED_TRANSITIONS, AppointmentStatus
from app.services.video import consult_room_name


async def book(
    db: AsyncSession,
    *,
    patient_id: str,
    specialty: str,
    scheduled_for: datetime | None = None,
    referral_id: str | None = None,
    triage_id: str | None = None,
    notes: str | None = None,
    booked_by: str | None = None,
    provider_id: str | None = None,
) -> Appointment:
    appt = Appointment(
        id=new_id("apt"),
        patient_id=patient_id,
        provider_id=provider_id,
        specialty=specialty,
        scheduled_for=scheduled_for,
        status=AppointmentStatus.requested.value,
        referral_id=referral_id,
        triage_id=triage_id,
        notes=notes,
        booked_by=booked_by,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt


async def get(db: AsyncSession, appointment_id: str) -> Appointment:
    appt = (
        await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    ).scalar_one_or_none()
    if appt is None:
        raise not_found("Appointment", appointment_id)
    return appt


async def transition(
    db: AsyncSession,
    appt: Appointment,
    action: str,
    *,
    actor_role: str,
    is_owner: bool,
    provider: Provider | None = None,
) -> Appointment:
    """Apply `action` to `appt`, validating against ALLOWED_TRANSITIONS.

    `actor_role` is the caller's role; `is_owner` is True when the caller is the
    patient who booked this appointment (needed because patient actions are
    scoped to their own record). `provider` is the acting provider row (used to
    stamp provider_id + build the consult room on accept).
    """
    rule = ALLOWED_TRANSITIONS.get(action)
    if rule is None:
        raise AppError(
            VALIDATION_ERROR,
            f"Unknown appointment action: {action!r}",
            details={"allowed": sorted(ALLOWED_TRANSITIONS)},
            retryable=False,
            status_code=400,
        )

    # Role gate. "patient" actions require the caller to own the appointment.
    if actor_role not in rule["roles"]:
        raise AppError(
            FORBIDDEN,
            f"Role {actor_role!r} may not {action} an appointment",
            retryable=False,
        )
    if actor_role == "patient" and not is_owner:
        raise AppError(
            FORBIDDEN,
            "You can only modify your own appointment",
            retryable=False,
        )

    # Legal-edge gate.
    current = AppointmentStatus(appt.status)
    if current not in rule["from"]:
        raise AppError(
            VALIDATION_ERROR,
            f"Cannot {action} an appointment in status {current.value!r}",
            details={"from": current.value, "allowed_from": [s.value for s in rule["from"]]},
            retryable=False,
            status_code=400,
        )

    target: AppointmentStatus = rule["to"]

    # Side effects on accept: assign provider, room, and an in-app reminder.
    if target is AppointmentStatus.accepted and provider is not None:
        appt.provider_id = provider.id
        appt.consult_room = consult_room_name(appt.patient_id, appt.id)
        await _append_appointment_reminder(db, appt)

    appt.status = target.value
    await db.commit()
    await db.refresh(appt)
    return appt


async def _append_appointment_reminder(db: AsyncSession, appt: Appointment) -> None:
    """Append (never replace) an in-app 'Upcoming' reminder for an accepted
    appointment. Deliberately does NOT use persistence.replace_reminders, which
    wipes the patient's medication schedule — appointments coexist with those."""
    schedule: dict = {"appointment_id": appt.id, "specialty": appt.specialty}
    if appt.scheduled_for is not None:
        schedule["scheduled_for"] = appt.scheduled_for.isoformat()
    if appt.consult_room:
        schedule["consult_room"] = appt.consult_room
    db.add(
        ReminderRow(
            id=new_id("rem", 5),
            patient_id=appt.patient_id,
            reminder_type="appointment",
            label=f"Consultation: {appt.specialty}",
            schedule=schedule,
            needs_confirmation=False,
        )
    )
    await db.flush()


async def list_for_role(
    db: AsyncSession,
    *,
    role: str,
    actor_id: str,
    provider: Provider | None = None,
    status: str | None = None,
) -> list[Appointment]:
    """Role-scoped listing.

    patient  → appointments they own (actor_id == patient_id).
    provider → assigned to them OR matching their specialty with no provider yet
               (the unclaimed queue).
    other    → not supported here (health_worker arrives in F4).
    """
    if role == "patient":
        stmt = select(Appointment).where(Appointment.patient_id == actor_id)
    elif role == "provider":
        if provider is None:  # pragma: no cover — router always passes one
            raise AppError(FORBIDDEN, "Provider context required", retryable=False)
        queue = Appointment.provider_id.is_(None)
        if provider.specialty:
            queue = queue & (Appointment.specialty == provider.specialty)
        else:
            queue = False  # no specialty set → only explicitly-assigned ones
        stmt = select(Appointment).where(
            or_(Appointment.provider_id == provider.id, queue)
        )
    elif role == "health_worker":
        from app.db.models import PatientLink

        linked = select(PatientLink.patient_id).where(
            PatientLink.health_worker_id == actor_id,
            PatientLink.active.is_(True),
        )
        stmt = select(Appointment).where(Appointment.patient_id.in_(linked))
    else:
        raise AppError(
            VALIDATION_ERROR,
            f"Listing not supported for role {role!r}",
            retryable=False,
            status_code=400,
        )

    if status is not None:
        stmt = stmt.where(Appointment.status == status)
    stmt = stmt.order_by(Appointment.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def to_dto_fields(db: AsyncSession, appt: Appointment) -> dict:
    """Resolve joined provider info for the DTO (single extra query when assigned)."""
    provider_name = None
    provider_specialty = None
    if appt.provider_id:
        provider = (
            await db.execute(select(Provider).where(Provider.id == appt.provider_id))
        ).scalar_one_or_none()
        if provider is not None:
            provider_name = provider.display_name
            provider_specialty = provider.specialty
    return {"provider_name": provider_name, "provider_specialty": provider_specialty}
