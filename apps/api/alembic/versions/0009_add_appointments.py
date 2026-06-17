"""add appointments table (Phase 6 F2 — specialist scheduling)

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("provider_id", sa.String(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("specialty", sa.String(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), server_default="requested"),
        sa.Column("consult_room", sa.String(), nullable=True),
        sa.Column("referral_id", sa.String(), sa.ForeignKey("referrals.id"), nullable=True),
        sa.Column("triage_id", sa.String(), sa.ForeignKey("triage_results.id"), nullable=True),
        sa.Column("booked_by", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_appt_patient", "appointments", ["patient_id"])
    op.create_index("ix_appt_provider", "appointments", ["provider_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_appt_provider", table_name="appointments")
    op.drop_index("ix_appt_patient", table_name="appointments")
    op.drop_table("appointments")
