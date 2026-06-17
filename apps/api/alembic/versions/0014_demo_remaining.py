"""Demo remaining: in-app notifications, appointment exceptions, follow-ups.

Revision ID: 0014
Revises: 0013
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "in_app_notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("data", json_type, nullable=True),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_in_app_notif_user", "in_app_notifications", ["user_id", "status", "created_at"])

    op.add_column("appointments", sa.Column("cancellation_reason", sa.String(), nullable=True))
    op.add_column("appointments", sa.Column("rescheduled_from_id", sa.String(), nullable=True))
    op.add_column("appointments", sa.Column("follow_up_for_appointment_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "follow_up_for_appointment_id")
    op.drop_column("appointments", "rescheduled_from_id")
    op.drop_column("appointments", "cancellation_reason")
    op.drop_index("ix_in_app_notif_user", table_name="in_app_notifications")
    op.drop_table("in_app_notifications")
