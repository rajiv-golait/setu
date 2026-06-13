"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("lang_pref", sa.String(), server_default="mr"),
        sa.Column("patient_token", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("doc_type", sa.String(), nullable=True),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("mime", sa.String(), nullable=True),
        sa.Column("source", sa.String(), server_default="upload"),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "extractions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id")),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("raw_json", JSONB, nullable=False),
        sa.Column("overall_confidence", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id")),
        sa.Column("claim_type", sa.String(), nullable=False),
        sa.Column("normalized_key", sa.String(), nullable=False),
        sa.Column("fields", JSONB, nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=False),
        sa.Column("observed_at", sa.Date(), nullable=True),
        sa.Column("needs_review", sa.Boolean(), server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_claims_grouping", "claims",
        ["patient_id", "claim_type", "normalized_key", "observed_at"],
    )

    op.create_table(
        "current_truth",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("normalized_key", sa.String(), nullable=False),
        sa.Column("value", JSONB, nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("state", sa.String(), server_default="confirmed"),
        sa.Column("source_claim_ids", JSONB, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("patient_id", "entry_type", "normalized_key", name="uq_truth_entry"),
    )

    op.create_table(
        "briefs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("brief_json", JSONB, nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("lang", sa.String(), server_default="mr"),
        sa.Column("summary_json", JSONB, nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "shares",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("snapshot_json", JSONB, nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("brief_id", sa.String(), sa.ForeignKey("briefs.id"), nullable=True),
        sa.Column("specialty", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("snapshot_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in (
        "referrals", "shares", "summaries", "briefs",
        "current_truth", "claims", "extractions", "documents", "patients",
    ):
        op.drop_table(table)
