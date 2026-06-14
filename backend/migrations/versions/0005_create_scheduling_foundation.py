"""Create the initial scheduling foundation.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_students_id_academy_id",
        "students",
        ["id", "academy_id"],
    )

    op.create_table(
        "classes",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("class_code", sa.String(length=50), nullable=False),
        sa.Column("class_name", sa.String(length=200), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column("updated_by", UUID, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_classes_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "branch_id",
            "class_code",
            name="uq_classes_branch_code",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_classes_id_academy_branch",
        ),
    )
    op.create_index(
        "ix_classes_academy_branch_status",
        "classes",
        ["academy_id", "branch_id", "status"],
    )

    op.create_table(
        "rooms",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("room_code", sa.String(length=50), nullable=False),
        sa.Column("room_name", sa.String(length=200), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column("updated_by", UUID, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_rooms_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "branch_id",
            "room_code",
            name="uq_rooms_branch_code",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_rooms_id_academy_branch",
        ),
    )
    op.create_index(
        "ix_rooms_academy_branch_status",
        "rooms",
        ["academy_id", "branch_id", "status"],
    )

    op.create_table(
        "class_students",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("class_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("enrollment_status", sa.String(length=30), nullable=False),
        sa.Column("enrolled_by", UUID, nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_class_students_class_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_class_students_student_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_class_students_class_student",
        ),
    )
    op.create_index(
        "ix_class_students_student_status",
        "class_students",
        ["academy_id", "student_id", "enrollment_status"],
    )

    op.create_table(
        "schedules",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("class_id", UUID, nullable=False),
        sa.Column("teacher_id", UUID, nullable=False),
        sa.Column("room_id", UUID, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column("updated_by", UUID, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_schedules_branch_academy",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_schedules_class_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_schedules_teacher_academy",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["room_id", "academy_id", "branch_id"],
            ["rooms.id", "rooms.academy_id", "rooms.branch_id"],
            name="fk_schedules_room_scope",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_schedules_id_academy_branch",
        ),
    )
    op.create_index(
        "ix_schedules_teacher_window",
        "schedules",
        ["academy_id", "teacher_id", "starts_at", "ends_at", "status"],
    )
    op.create_index(
        "ix_schedules_room_window",
        "schedules",
        ["academy_id", "branch_id", "room_id", "starts_at", "ends_at", "status"],
    )
    op.create_index(
        "ix_schedules_class_window",
        "schedules",
        ["academy_id", "class_id", "starts_at", "ends_at", "status"],
    )

    op.create_table(
        "class_sessions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("schedule_id", UUID, nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("actual_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_class_sessions_schedule_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "schedule_id",
            name="uq_class_sessions_schedule",
        ),
    )
    op.create_index(
        "ix_class_sessions_academy_branch_status",
        "class_sessions",
        ["academy_id", "branch_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_class_sessions_academy_branch_status",
        table_name="class_sessions",
    )
    op.drop_table("class_sessions")
    op.drop_index("ix_schedules_class_window", table_name="schedules")
    op.drop_index("ix_schedules_room_window", table_name="schedules")
    op.drop_index("ix_schedules_teacher_window", table_name="schedules")
    op.drop_table("schedules")
    op.drop_index(
        "ix_class_students_student_status",
        table_name="class_students",
    )
    op.drop_table("class_students")
    op.drop_index("ix_rooms_academy_branch_status", table_name="rooms")
    op.drop_table("rooms")
    op.drop_index("ix_classes_academy_branch_status", table_name="classes")
    op.drop_table("classes")
    op.drop_constraint(
        "uq_students_id_academy_id",
        "students",
        type_="unique",
    )
