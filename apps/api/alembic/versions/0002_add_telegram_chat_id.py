"""add telegram_chat_id to patients

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("telegram_chat_id", sa.String(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_patients_telegram_chat_id", "patients", ["telegram_chat_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_patients_telegram_chat_id", "patients", type_="unique")
    op.drop_column("patients", "telegram_chat_id")
