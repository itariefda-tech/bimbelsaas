"""Create academies and branches, then bind authentication scopes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_academies_status", "academies", ["status"])

    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("address", sa.String(length=1000), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_branches_academy_id_academies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "code",
            name="uq_branches_academy_code",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            name="uq_branches_id_academy_id",
        ),
    )
    op.create_index(
        "ix_branches_academy_status",
        "branches",
        ["academy_id", "status"],
    )

    op.create_foreign_key(
        "fk_users_academy_id_academies",
        "users",
        "academies",
        ["academy_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_role_assignments_academy_id_academies",
        "role_assignments",
        "academies",
        ["academy_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_role_assignments_branch_academy_branches",
        "role_assignments",
        "branches",
        ["branch_id", "academy_id"],
        ["id", "academy_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_role_assignments_branch_academy_branches",
        "role_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_role_assignments_academy_id_academies",
        "role_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_users_academy_id_academies",
        "users",
        type_="foreignkey",
    )
    op.drop_index("ix_branches_academy_status", table_name="branches")
    op.drop_table("branches")
    op.drop_index("ix_academies_status", table_name="academies")
    op.drop_table("academies")
