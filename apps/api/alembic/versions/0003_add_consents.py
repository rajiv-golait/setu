"""add consents table (DPDP consent gateway)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("consent_text", sa.String(), nullable=False),
        sa.Column("lang", sa.String(), server_default="mr"),
        sa.Column("channel", sa.String(), server_default="web"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_consents_patient_purpose", "consents", ["patient_id", "purpose"]
    )


def downgrade() -> None:
    op.drop_index("ix_consents_patient_purpose", table_name="consents")
    op.drop_table("consents")
