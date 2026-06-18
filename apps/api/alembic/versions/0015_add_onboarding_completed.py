"""Add patients.onboarding_completed — persist language onboarding across logins.

Revision ID: 0015
Revises: 0014
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Existing accounts already chose a language; don't force onboarding again.
    op.execute("UPDATE patients SET onboarding_completed = true")


def downgrade() -> None:
    op.drop_column("patients", "onboarding_completed")
