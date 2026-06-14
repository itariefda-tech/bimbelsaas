"""Create teacher and student branch foundations.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_users_id_academy_id",
        "users",
        ["id", "academy_id"],
    )

    op.create_table(
        "teachers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("teacher_code", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("employment_status", sa.String(length=30), nullable=False),
        sa.Column("specialization", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_teachers_academy_id_academies",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_teachers_user_academy_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "teacher_code",
            name="uq_teachers_academy_code",
        ),
        sa.UniqueConstraint(
            "academy_id",
            "user_id",
            name="uq_teachers_academy_user",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            name="uq_teachers_id_academy_id",
        ),
    )
    op.create_index(
        "ix_teachers_academy_status",
        "teachers",
        ["academy_id", "status"],
    )

    op.create_table(
        "teacher_branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_status", sa.String(length=30), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_teacher_branches_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_teacher_branches_teacher_academy_teachers",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "teacher_id",
            "branch_id",
            name="uq_teacher_branches_teacher_branch",
        ),
    )
    op.create_index(
        "ix_teacher_branches_academy_branch_status",
        "teacher_branches",
        ["academy_id", "branch_id", "assignment_status"],
    )

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("home_branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("student_code", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_students_academy_id_academies",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["home_branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_students_home_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_students_user_academy_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "student_code",
            name="uq_students_academy_code",
        ),
        sa.UniqueConstraint(
            "academy_id",
            "user_id",
            name="uq_students_academy_user",
        ),
    )
    op.create_index(
        "ix_students_academy_home_branch_status",
        "students",
        ["academy_id", "home_branch_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_students_academy_home_branch_status",
        table_name="students",
    )
    op.drop_table("students")
    op.drop_index(
        "ix_teacher_branches_academy_branch_status",
        table_name="teacher_branches",
    )
    op.drop_table("teacher_branches")
    op.drop_index("ix_teachers_academy_status", table_name="teachers")
    op.drop_table("teachers")
    op.drop_constraint(
        "uq_users_id_academy_id",
        "users",
        type_="unique",
    )
