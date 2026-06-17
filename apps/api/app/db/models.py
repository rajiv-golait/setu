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
    """Phase 1 — clinician/specialist account. Role lives in Supabase
    app_metadata.role='provider'; this row holds the provider profile that the
    doctor-side of appointments (F2) and the doctor portal read. Auto-provisioned
    on first GET /providers/me (same pattern as patient GET /me)."""

    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # prv_xxxx
    supabase_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    facility: Mapped[str | None] = mapped_column(String, nullable=True)  # clinic/hospital
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
    booked_by: Mapped[str | None] = mapped_column(String, nullable=True)  # patient|health_worker|provider actor id
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
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
