"""Create beta launch onboarding and feedback tables.

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "beta_academy_onboardings",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("cohort_label", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("operational_owner_name", sa.String(200), nullable=False),
        sa.Column("operational_owner_contact", sa.String(200), nullable=False),
        sa.Column("success_criteria", JSON, nullable=False),
        sa.Column("target_start_date", sa.Date(), nullable=True),
        sa.Column("target_end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("updated_by", UUID, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_beta_onboardings_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_beta_onboardings_status",
        "beta_academy_onboardings",
        ["status", "target_start_date"],
    )
    op.create_index(
        "ix_beta_onboardings_academy_status",
        "beta_academy_onboardings",
        ["academy_id", "status"],
    )
    op.create_table(
        "beta_feedback",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=True),
        sa.Column("reporter_user_id", UUID, nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source_role", sa.String(50), nullable=False),
        sa.Column("summary", sa.String(200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_beta_feedback_academy",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_beta_feedback_branch_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_beta_feedback_reporter_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_beta_feedback_academy_status",
        "beta_feedback",
        ["academy_id", "status"],
    )
    op.create_index(
        "ix_beta_feedback_branch_status",
        "beta_feedback",
        ["branch_id", "status"],
    )
    op.create_index(
        "ix_beta_feedback_severity_created",
        "beta_feedback",
        ["severity", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_beta_feedback_severity_created", table_name="beta_feedback")
    op.drop_index("ix_beta_feedback_branch_status", table_name="beta_feedback")
    op.drop_index("ix_beta_feedback_academy_status", table_name="beta_feedback")
    op.drop_table("beta_feedback")
    op.drop_index(
        "ix_beta_onboardings_academy_status",
        table_name="beta_academy_onboardings",
    )
    op.drop_index(
        "ix_beta_onboardings_status",
        table_name="beta_academy_onboardings",
    )
    op.drop_table("beta_academy_onboardings")
