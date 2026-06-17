"""add triage_results table (Phase 6 F1 — non-diagnostic routing)

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "triage_results",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("inputs", JSONB, nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("recommendation", sa.String(), nullable=False),
        sa.Column("rationale", JSONB, nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("lang", sa.String(), server_default="mr"),
        sa.Column("engine_version", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_triage_patient", "triage_results", ["patient_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_triage_patient", table_name="triage_results")
    op.drop_table("triage_results")
