"""add vitals table (Phase 6 F5)

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vitals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("vital_type", sa.String(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("flag", sa.String(), nullable=True),
        sa.Column("recorded_by", sa.String(), nullable=True),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_vitals_patient_type", "vitals", ["patient_id", "vital_type", "measured_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_vitals_patient_type", table_name="vitals")
    op.drop_table("vitals")
