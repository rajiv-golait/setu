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
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Index,
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
    patient_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    doc_type: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    mime: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="upload")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|extracted|failed
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


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    brief_id: Mapped[str | None] = mapped_column(ForeignKey("briefs.id"), nullable=True)
    specialty: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
