"""Create parent profiles and explicit student relationships.

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "parents",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("primary_contact", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_parents_user_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "user_id",
            name="uq_parents_academy_user",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            name="uq_parents_id_academy",
        ),
    )
    op.create_index(
        "ix_parents_academy_status",
        "parents",
        ["academy_id", "status"],
    )

    op.create_table(
        "parent_students",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("parent_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("relationship_status", sa.String(length=30), nullable=False),
        sa.Column("linked_by", UUID, nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id", "academy_id"],
            ["parents.id", "parents.academy_id"],
            name="fk_parent_students_parent_academy",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_parent_students_student_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_id",
            "student_id",
            name="uq_parent_students_parent_student",
        ),
    )
    op.create_index(
        "ix_parent_students_parent_status",
        "parent_students",
        ["academy_id", "parent_id", "relationship_status"],
    )
    op.create_index(
        "ix_parent_students_student_status",
        "parent_students",
        ["academy_id", "student_id", "relationship_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_parent_students_student_status",
        table_name="parent_students",
    )
    op.drop_index(
        "ix_parent_students_parent_status",
        table_name="parent_students",
    )
    op.drop_table("parent_students")
    op.drop_index("ix_parents_academy_status", table_name="parents")
    op.drop_table("parents")
