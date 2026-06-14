"""Create immutable schedule change requests.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "schedule_change_requests",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("schedule_id", UUID, nullable=False),
        sa.Column("replacement_schedule_id", UUID, nullable=True),
        sa.Column("original_class_id", UUID, nullable=False),
        sa.Column("original_teacher_id", UUID, nullable=False),
        sa.Column("original_room_id", UUID, nullable=False),
        sa.Column("original_starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("original_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("original_timezone", sa.String(length=100), nullable=False),
        sa.Column("original_status", sa.String(length=30), nullable=False),
        sa.Column("proposed_teacher_id", UUID, nullable=False),
        sa.Column("proposed_room_id", UUID, nullable=False),
        sa.Column("proposed_starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_timezone", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_by", UUID, nullable=False),
        sa.Column("requester_role", sa.String(length=50), nullable=False),
        sa.Column("decided_by", UUID, nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_schedule_change_requests_schedule_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["replacement_schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_schedule_change_requests_replacement_scope",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_schedule_change_requests_scope_status",
        "schedule_change_requests",
        ["academy_id", "branch_id", "status"],
    )
    op.create_index(
        "ix_schedule_change_requests_schedule_status",
        "schedule_change_requests",
        ["schedule_id", "status"],
    )
    op.create_index(
        "uq_schedule_change_requests_one_pending",
        "schedule_change_requests",
        ["schedule_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_schedule_change_requests_one_pending",
        table_name="schedule_change_requests",
    )
    op.drop_index(
        "ix_schedule_change_requests_schedule_status",
        table_name="schedule_change_requests",
    )
    op.drop_index(
        "ix_schedule_change_requests_scope_status",
        table_name="schedule_change_requests",
    )
    op.drop_table("schedule_change_requests")
