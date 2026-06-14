"""Create lesson summary lifecycle and edit approval workflow.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "lesson_summaries",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("session_id", UUID, nullable=False),
        sa.Column("schedule_id", UUID, nullable=False),
        sa.Column("class_id", UUID, nullable=False),
        sa.Column("teacher_id", UUID, nullable=False),
        sa.Column("lesson_topic", sa.String(length=300), nullable=False),
        sa.Column("class_summary", sa.String(length=2000), nullable=False),
        sa.Column("teacher_notes", sa.String(length=2000), nullable=True),
        sa.Column("homework", sa.String(length=1000), nullable=True),
        sa.Column(
            "student_attention_notes",
            sa.String(length=2000),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("updated_by", UUID, nullable=False),
        sa.Column("published_by", UUID, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id", "academy_id", "branch_id"],
            [
                "class_sessions.id",
                "class_sessions.academy_id",
                "class_sessions.branch_id",
            ],
            name="fk_lesson_summaries_session_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_lesson_summaries_teacher_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            name="uq_lesson_summaries_session",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_lesson_summaries_id_academy_branch",
        ),
    )
    op.create_index(
        "ix_lesson_summaries_scope_status",
        "lesson_summaries",
        ["academy_id", "branch_id", "status"],
    )

    op.create_table(
        "lesson_summary_edit_requests",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("lesson_summary_id", UUID, nullable=False),
        sa.Column("original_data", JSON, nullable=False),
        sa.Column("proposed_data", JSON, nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_by", UUID, nullable=False),
        sa.Column("decided_by", UUID, nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["lesson_summary_id", "academy_id", "branch_id"],
            [
                "lesson_summaries.id",
                "lesson_summaries.academy_id",
                "lesson_summaries.branch_id",
            ],
            name="fk_lesson_summary_edit_requests_summary_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lesson_summary_edit_requests_scope_status",
        "lesson_summary_edit_requests",
        ["academy_id", "branch_id", "status"],
    )
    op.create_index(
        "uq_lesson_summary_edit_requests_one_pending",
        "lesson_summary_edit_requests",
        ["lesson_summary_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_lesson_summary_edit_requests_one_pending",
        table_name="lesson_summary_edit_requests",
    )
    op.drop_index(
        "ix_lesson_summary_edit_requests_scope_status",
        table_name="lesson_summary_edit_requests",
    )
    op.drop_table("lesson_summary_edit_requests")
    op.drop_index(
        "ix_lesson_summaries_scope_status",
        table_name="lesson_summaries",
    )
    op.drop_table("lesson_summaries")
