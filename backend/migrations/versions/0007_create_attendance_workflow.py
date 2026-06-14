"""Create attendance lifecycle and edit approval workflow.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_class_sessions_id_academy_branch",
        "class_sessions",
        ["id", "academy_id", "branch_id"],
    )
    op.add_column(
        "class_sessions",
        sa.Column(
            "attendance_status",
            sa.String(length=30),
            server_default="draft",
            nullable=False,
        ),
    )
    op.add_column(
        "class_sessions",
        sa.Column("attendance_finalized_by", UUID, nullable=True),
    )
    op.add_column(
        "class_sessions",
        sa.Column(
            "attendance_finalized_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.alter_column("class_sessions", "attendance_status", server_default=None)

    op.create_table(
        "attendances",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("session_id", UUID, nullable=False),
        sa.Column("schedule_id", UUID, nullable=False),
        sa.Column("class_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("attendance_status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("recorded_by", UUID, nullable=False),
        sa.Column("updated_by", UUID, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id", "academy_id", "branch_id"],
            [
                "class_sessions.id",
                "class_sessions.academy_id",
                "class_sessions.branch_id",
            ],
            name="fk_attendances_session_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_attendances_student_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "student_id",
            name="uq_attendances_session_student",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_attendances_id_academy_branch",
        ),
    )
    op.create_index(
        "ix_attendances_scope_session",
        "attendances",
        ["academy_id", "branch_id", "session_id"],
    )
    op.create_index(
        "ix_attendances_student_recorded",
        "attendances",
        ["academy_id", "student_id", "recorded_at"],
    )

    op.create_table(
        "attendance_edit_requests",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("attendance_id", UUID, nullable=False),
        sa.Column("original_status", sa.String(length=30), nullable=False),
        sa.Column("original_note", sa.String(length=500), nullable=True),
        sa.Column("proposed_status", sa.String(length=30), nullable=False),
        sa.Column("proposed_note", sa.String(length=500), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_by", UUID, nullable=False),
        sa.Column("decided_by", UUID, nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["attendance_id", "academy_id", "branch_id"],
            ["attendances.id", "attendances.academy_id", "attendances.branch_id"],
            name="fk_attendance_edit_requests_attendance_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attendance_edit_requests_scope_status",
        "attendance_edit_requests",
        ["academy_id", "branch_id", "status"],
    )
    op.create_index(
        "uq_attendance_edit_requests_one_pending",
        "attendance_edit_requests",
        ["attendance_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_attendance_edit_requests_one_pending",
        table_name="attendance_edit_requests",
    )
    op.drop_index(
        "ix_attendance_edit_requests_scope_status",
        table_name="attendance_edit_requests",
    )
    op.drop_table("attendance_edit_requests")
    op.drop_index("ix_attendances_student_recorded", table_name="attendances")
    op.drop_index("ix_attendances_scope_session", table_name="attendances")
    op.drop_table("attendances")
    op.drop_column("class_sessions", "attendance_finalized_at")
    op.drop_column("class_sessions", "attendance_finalized_by")
    op.drop_column("class_sessions", "attendance_status")
    op.drop_constraint(
        "uq_class_sessions_id_academy_branch",
        "class_sessions",
        type_="unique",
    )
