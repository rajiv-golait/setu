"""add supabase_user_id to patients (product auth link)

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("supabase_user_id", sa.String(), nullable=True))
    op.create_index("ix_patients_supabase_user_id", "patients", ["supabase_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_patients_supabase_user_id", table_name="patients")
    op.drop_column("patients", "supabase_user_id")
