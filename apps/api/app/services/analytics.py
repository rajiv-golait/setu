"""Read-only admin analytics aggregations — no PII."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, Patient, TriageResult
from app.schemas.analytics import AnalyticsOverviewDTO, LanguageCount


async def overview(
    db: AsyncSession,
    *,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> AnalyticsOverviewDTO:
    appt_filters = []
    patient_filters = []
    triage_filters = []
    if from_dt is not None:
        appt_filters.append(Appointment.created_at >= from_dt)
        patient_filters.append(Patient.created_at >= from_dt)
        triage_filters.append(TriageResult.created_at >= from_dt)
    if to_dt is not None:
        appt_filters.append(Appointment.created_at <= to_dt)
        patient_filters.append(Patient.created_at <= to_dt)
        triage_filters.append(TriageResult.created_at <= to_dt)

    consultations_completed = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.status == "completed", *appt_filters)
        )
    ).scalar_one()

    rural_patients = (
        await db.execute(
            select(func.count())
            .select_from(Patient)
            .where(Patient.is_rural.is_(True), *patient_filters)
        )
    ).scalar_one()

    total_patients = (
        await db.execute(
            select(func.count()).select_from(Patient).where(*patient_filters)
        )
    ).scalar_one()

    lang_rows = (
        await db.execute(
            select(Patient.lang_pref, func.count())
            .where(*patient_filters)
            .group_by(Patient.lang_pref)
        )
    ).all()
    languages = [LanguageCount(lang_pref=row[0] or "unknown", count=row[1]) for row in lang_rows]

    referral_total = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.referral_id.is_not(None), *appt_filters)
        )
    ).scalar_one()

    referral_done = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.referral_id.is_not(None),
                Appointment.status.in_(("accepted", "confirmed", "completed")),
                *appt_filters,
            )
        )
    ).scalar_one()

    referral_completion_rate = (
        float(referral_done) / referral_total if referral_total else 0.0
    )

    high_priority_triage = (
        await db.execute(
            select(func.count())
            .select_from(TriageResult)
            .where(TriageResult.priority == "high", *triage_filters)
        )
    ).scalar_one()

    avg_minutes: float | None = None
    completed = (
        await db.execute(
            select(Appointment.updated_at, Appointment.requested_at)
            .where(Appointment.status == "completed", *appt_filters)
        )
    ).all()
    if completed:
        deltas = []
        for updated_at, requested_at in completed:
            if updated_at and requested_at:
                deltas.append((updated_at - requested_at).total_seconds() / 60.0)
        if deltas:
            avg_minutes = sum(deltas) / len(deltas)

    return AnalyticsOverviewDTO(
        consultations_completed=consultations_completed,
        rural_patients=rural_patients,
        total_patients=total_patients,
        languages=languages,
        referral_completion_rate=referral_completion_rate,
        high_priority_triage=high_priority_triage,
        avg_consultation_minutes=avg_minutes,
    )
