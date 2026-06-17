"""Production platform: provider verification, scheduling, encounters, notifications.

Revision ID: 0013
Revises: 0012
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    # --- Provider profile extensions ---
    op.add_column(
        "providers",
        sa.Column("verification_status", sa.String(), server_default="pending", nullable=False),
    )
    op.add_column("providers", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("providers", sa.Column("approved_by", sa.String(), nullable=True))
    op.add_column("providers", sa.Column("experience_years", sa.Integer(), nullable=True))
    op.add_column("providers", sa.Column("languages", json_type, nullable=True))
    op.add_column("providers", sa.Column("location", sa.String(), nullable=True))
    op.add_column("providers", sa.Column("consultation_fee", sa.Numeric(), nullable=True))
    op.add_column("providers", sa.Column("bio", sa.String(), nullable=True))

    op.create_table(
        "provider_credentials",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "provider_access_grants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("appointment_id", sa.String(), sa.ForeignKey("appointments.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- Patient health profile ---
    op.create_table(
        "patient_profiles",
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), primary_key=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("blood_group", sa.String(), nullable=True),
        sa.Column("allergies_known", json_type, nullable=True),
        sa.Column("chronic_conditions", json_type, nullable=True),
        sa.Column("emergency_contact", json_type, nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- Scheduling ---
    op.create_table(
        "provider_availability",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(), nullable=False),
        sa.Column("end_time", sa.String(), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("timezone", sa.String(), server_default="Asia/Kolkata", nullable=False),
    )

    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.UniqueConstraint("provider_id", "starts_at", name="uq_slot_provider_start"),
    )

    op.add_column(
        "appointments",
        sa.Column("slot_id", sa.String(), sa.ForeignKey("appointment_slots.id"), nullable=True),
    )

    # --- Encounters & clinical records ---
    op.create_table(
        "consultation_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("appointment_id", sa.String(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("video_joined_patient_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("video_joined_provider_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "encounters",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("appointment_id", sa.String(), sa.ForeignKey("appointments.id"), nullable=True),
        sa.Column("encounter_type", sa.String(), server_default="tele", nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.Column("recording_consent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("encounter_id", sa.String(), sa.ForeignKey("encounters.id"), nullable=False),
        sa.Column("author_id", sa.String(), nullable=False),
        sa.Column("note_type", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("is_draft", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("encounter_id", sa.String(), sa.ForeignKey("encounters.id"), nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("items", json_type, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Notifications ---
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.UniqueConstraint("user_id", "channel", name="uq_notif_pref"),
    )

    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- Admin support ---
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("reporter_id", sa.String(), nullable=True),
        sa.Column("reporter_role", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.Column("assigned_to", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- AI observability ---
    op.create_table(
        "ai_request_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("provider_name", sa.String(), nullable=True),
        sa.Column("patient_id", sa.String(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("fallback_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column("documents", sa.Column("encryption_key_id", sa.String(), nullable=True))

    # Existing admin-granted providers are approved
    op.execute("UPDATE providers SET verification_status = 'approved' WHERE verification_status = 'pending'")


def downgrade() -> None:
    op.drop_column("documents", "encryption_key_id")
    op.drop_table("ai_request_logs")
    op.drop_table("support_tickets")
    op.drop_table("notification_outbox")
    op.drop_table("notification_preferences")
    op.drop_table("prescriptions")
    op.drop_table("clinical_notes")
    op.drop_table("encounters")
    op.drop_table("consultation_sessions")
    op.drop_column("appointments", "slot_id")
    op.drop_table("appointment_slots")
    op.drop_table("provider_availability")
    op.drop_table("patient_profiles")
    op.drop_table("provider_access_grants")
    op.drop_table("provider_credentials")
    for col in (
        "bio",
        "consultation_fee",
        "location",
        "languages",
        "experience_years",
        "approved_by",
        "approved_at",
        "verification_status",
    ):
        op.drop_column("providers", col)
