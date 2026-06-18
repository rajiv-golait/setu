"""ORM models. Mirrors the locked PostgreSQL schema.

Conventions:
- text PKs (readable prefixed ids).
- claims are APPEND-ONLY (never updated/deleted).
- current_truth is DERIVED (upserted by the reducer each run).
- job state is NOT here — it lives in Redis only.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base

# Use JSONB on Postgres, fall back to generic JSON elsewhere (e.g. sqlite tests).
JSONType = JSONB().with_variant(JSON(), "sqlite")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    lang_pref: Mapped[str] = mapped_column(String, default="mr")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    patient_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    supabase_user_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    registered_by_worker_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("health_workers.id"), nullable=True
    )
    is_rural: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    doc_type: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    encryption_key_id: Mapped[str | None] = mapped_column(String, nullable=True)
    mime: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="upload")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|extracted|failed|purged
    # Retention: the raw image is transient (purged after the retention window or
    # on request). original_hash is kept permanently so claims remain auditable
    # to the source even after the raw file is gone (DPDP erasure + trust).
    original_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Extraction(Base):
    """Raw provider output — audit trail."""

    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    overall_confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Claim(Base):
    """APPEND-ONLY atomic assertions. Never update or delete."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    claim_type: Mapped[str] = mapped_column(String, nullable=False)
    normalized_key: Mapped[str] = mapped_column(String, nullable=False)
    fields: Mapped[dict] = mapped_column(JSONType, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric, nullable=False)
    observed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_claims_grouping", "patient_id", "claim_type", "normalized_key", "observed_at"),
    )


class CurrentTruth(Base):
    """DERIVED snapshot. Upserted by the reducer over ALL claims each run."""

    __tablename__ = "current_truth"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    entry_type: Mapped[str] = mapped_column(String, nullable=False)
    normalized_key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[dict] = mapped_column(JSONType, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    state: Mapped[str] = mapped_column(String, default="confirmed")
    source_claim_ids: Mapped[list] = mapped_column(JSONType, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("patient_id", "entry_type", "normalized_key", name="uq_truth_entry"),
    )


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    brief_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    lang: Mapped[str] = mapped_column(String, default="mr")
    summary_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Share(Base):
    __tablename__ = "shares"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONType, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Consent(Base):
    """DPDP consent record. Written BEFORE any document enters the pipeline."""

    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    purpose: Mapped[str] = mapped_column(String, nullable=False)  # e.g. document_processing
    consent_text: Mapped[str] = mapped_column(String, nullable=False)
    lang: Mapped[str] = mapped_column(String, default="mr")
    channel: Mapped[str] = mapped_column(String, default="web")  # web|telegram
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_consents_patient_purpose", "patient_id", "purpose"),
    )


class Reminder(Base):
    """Deterministic reminder schedule entry (B6). Restates the doctor's
    prescribed timing only — never an invented schedule. Delivery is out of
    scope (no push); this table is the schedule of record."""

    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    reminder_type: Mapped[str] = mapped_column(String, nullable=False)  # medication|lab_test_due|refill_due
    label: Mapped[str] = mapped_column(String, nullable=False)
    schedule: Mapped[dict] = mapped_column(JSONType, nullable=False)  # times/food/due_date/etc.
    source_claim_id: Mapped[str | None] = mapped_column(String, nullable=True)
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_reminders_patient", "patient_id"),
    )


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    brief_id: Mapped[str | None] = mapped_column(ForeignKey("briefs.id"), nullable=True)
    specialty: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Provider(Base):
    """Clinician/specialist account. Role in Supabase app_metadata.role='provider'."""

    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # prv_xxxx
    supabase_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    facility: Mapped[str | None] = mapped_column(String, nullable=True)
    verification_status: Mapped[str] = mapped_column(String, default="pending")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    consultation_fee: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    bio: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProviderAccessGrant(Base):
    __tablename__ = "provider_access_grants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    appointment_id: Mapped[str | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), primary_key=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String, nullable=True)
    allergies_known: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    chronic_conditions: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    emergency_contact: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    district: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProviderAvailability(Base):
    __tablename__ = "provider_availability"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String, nullable=False)
    end_time: Mapped[str] = mapped_column(String, nullable=False)
    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)
    timezone: Mapped[str] = mapped_column(String, default="Asia/Kolkata")


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="open")

    __table_args__ = (UniqueConstraint("provider_id", "starts_at", name="uq_slot_provider_start"),)


class ConsultationSession(Base):
    __tablename__ = "consultation_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    appointment_id: Mapped[str] = mapped_column(ForeignKey("appointments.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    video_joined_patient_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    video_joined_provider_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    appointment_id: Mapped[str | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)
    encounter_type: Mapped[str] = mapped_column(String, default="tele")
    status: Mapped[str] = mapped_column(String, default="open")
    recording_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    encounter_id: Mapped[str] = mapped_column(ForeignKey("encounters.id"))
    author_id: Mapped[str] = mapped_column(String, nullable=False)
    note_type: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    encounter_id: Mapped[str] = mapped_column(ForeignKey("encounters.id"))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    items: Mapped[dict] = mapped_column(JSONType, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_notif_pref"),)


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InAppNotification(Base):
    __tablename__ = "in_app_notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    reporter_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reporter_role: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open")
    assigned_to: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AiRequestLog(Base):
    __tablename__ = "ai_request_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_type: Mapped[str] = mapped_column(String, nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String, nullable=True)
    patient_id: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Appointment(Base):
    """Phase 6 F2 — specialist consultation booking.

    Lifecycle (validated in services/appointments.py, never by free status writes):
    requested → accepted → confirmed → completed, plus declined/cancelled. On
    accept the provider gets a deterministic Jitsi room (services/video.py) and an
    in-app "Upcoming" reminder row is appended — no push worker."""

    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # apt_xxxx
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    provider_id: Mapped[str | None] = mapped_column(ForeignKey("providers.id"), nullable=True)
    specialty: Mapped[str] = mapped_column(String, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="requested")
    consult_room: Mapped[str | None] = mapped_column(String, nullable=True)
    referral_id: Mapped[str | None] = mapped_column(ForeignKey("referrals.id"), nullable=True)
    triage_id: Mapped[str | None] = mapped_column(ForeignKey("triage_results.id"), nullable=True)
    booked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    slot_id: Mapped[str | None] = mapped_column(ForeignKey("appointment_slots.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    rescheduled_from_id: Mapped[str | None] = mapped_column(String, nullable=True)
    follow_up_for_appointment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        Index("ix_appt_patient", "patient_id"),
        Index("ix_appt_provider", "provider_id", "status"),
    )


class TriageResult(Base):
    """Phase 6 F1 — NON-DIAGNOSTIC routing decision.

    priority + recommendation are computed by a DETERMINISTIC rules table
    (services/triage_service.py), exactly like the priority.py posture. The
    reasoner is used ONLY to rephrase the already-decided recommendation into
    the patient's language; it never decides acuity, names a disease, or
    suggests a drug. This is care routing, not medicine — NEVER a diagnosis.
    """

    __tablename__ = "triage_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    inputs: Mapped[dict] = mapped_column(JSONType, nullable=False)  # symptoms/age/conditions/doc_ids
    priority: Mapped[str] = mapped_column(String, nullable=False)  # low|medium|high
    recommendation: Mapped[str] = mapped_column(
        String, nullable=False
    )  # visit_phc|schedule_specialist|emergency
    rationale: Mapped[dict] = mapped_column(JSONType, nullable=False)  # matched rule ids + factors
    message: Mapped[str | None] = mapped_column(String, nullable=True)  # lang-aware phrasing (never overrides)
    lang: Mapped[str] = mapped_column(String, default="mr")
    engine_version: Mapped[str] = mapped_column(String, nullable=False)  # ruleset version — auditability
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)  # patient|health_worker actor id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (Index("ix_triage_patient", "patient_id", "created_at"),)


class AccessLog(Base):
    """Who accessed a patient's data and when — DPDP audit trail."""

    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    resource: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (Index("ix_access_patient", "patient_id", "created_at"),)


class HealthWorker(Base):
    """ASHA/PHC worker. Role in Supabase app_metadata.role='health_worker'."""

    __tablename__ = "health_workers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    supabase_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    facility: Mapped[str | None] = mapped_column(String, nullable=True)
    phc_code: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PatientLink(Base):
    """Worker→patient association authorizing proxy actions."""

    __tablename__ = "patient_links"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    health_worker_id: Mapped[str] = mapped_column(ForeignKey("health_workers.id"))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    relationship: Mapped[str] = mapped_column(String, default="registered_by")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("health_worker_id", "patient_id", name="uq_worker_patient"),
    )


class Vital(Base):
    """Patient-recorded vital sign. Informational only — NOT diagnosed."""

    __tablename__ = "vitals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    vital_type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[dict] = mapped_column(JSONType, nullable=False)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    flag: Mapped[str | None] = mapped_column(String, nullable=True)
    recorded_by: Mapped[str | None] = mapped_column(String, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_vitals_patient_type", "patient_id", "vital_type", "measured_at"),
    )


class PushSubscription(Base):
    """Browser Web Push subscription (VAPID). One per device per user."""

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String, nullable=False)
    auth: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
