"""add access_logs, health_workers, patient_links + patient rural columns

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "access_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column("actor_role", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("resource", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_access_patient", "access_logs", ["patient_id", "created_at"])

    op.create_table(
        "health_workers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("supabase_user_id", sa.String(), unique=True, nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("facility", sa.String(), nullable=True),
        sa.Column("phc_code", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column(
        "patients",
        sa.Column("registered_by_worker_id", sa.String(), nullable=True),
    )
    op.add_column(
        "patients",
        sa.Column("is_rural", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_foreign_key(
        "fk_patients_registered_by_worker",
        "patients",
        "health_workers",
        ["registered_by_worker_id"],
        ["id"],
    )

    op.create_table(
        "patient_links",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("health_worker_id", sa.String(), sa.ForeignKey("health_workers.id")),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id")),
        sa.Column("relationship", sa.String(), server_default="registered_by"),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("health_worker_id", "patient_id", name="uq_worker_patient"),
    )


def downgrade() -> None:
    op.drop_table("patient_links")
    op.drop_constraint("fk_patients_registered_by_worker", "patients", type_="foreignkey")
    op.drop_column("patients", "is_rural")
    op.drop_column("patients", "registered_by_worker_id")
    op.drop_table("health_workers")
    op.drop_index("ix_access_patient", table_name="access_logs")
    op.drop_table("access_logs")
