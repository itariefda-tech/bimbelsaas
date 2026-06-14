"""Create versioned materials, distributions, and notification boundary.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("material_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("material_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("archived_by", UUID, nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "academy_id",
            "material_code",
            name="uq_materials_academy_code",
        ),
        sa.UniqueConstraint(
            "id",
            "academy_id",
            name="uq_materials_id_academy",
        ),
    )
    op.create_index(
        "ix_materials_academy_status",
        "materials",
        ["academy_id", "status"],
    )

    op.create_table(
        "material_versions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("material_id", UUID, nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("version_label", sa.String(length=50), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("uploaded_by", UUID, nullable=False),
        sa.Column("approved_by", UUID, nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["material_id", "academy_id"],
            ["materials.id", "materials.academy_id"],
            name="fk_material_versions_material_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_id",
            "version_number",
            name="uq_material_versions_number",
        ),
        sa.UniqueConstraint(
            "id",
            "material_id",
            "academy_id",
            name="uq_material_versions_id_material_academy",
        ),
    )
    op.create_index(
        "ix_material_versions_material_status",
        "material_versions",
        ["material_id", "status", "version_number"],
    )

    op.create_table(
        "material_distributions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("material_id", UUID, nullable=False),
        sa.Column("version_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("class_id", UUID, nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("distributed_by", UUID, nullable=False),
        sa.Column("distributed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["material_id", "academy_id"],
            ["materials.id", "materials.academy_id"],
            name="fk_material_distributions_material_academy",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id", "material_id", "academy_id"],
            [
                "material_versions.id",
                "material_versions.material_id",
                "material_versions.academy_id",
            ],
            name="fk_material_distributions_version_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_material_distributions_branch_academy",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_material_distributions_class_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_id",
            "branch_id",
            "class_id",
            name="uq_material_distributions_target",
        ),
    )
    op.create_index(
        "ix_material_distributions_class_status",
        "material_distributions",
        ["academy_id", "branch_id", "class_id", "status"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("recipient_user_id", UUID, nullable=False),
        sa.Column("notification_type", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipient_user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_notifications_recipient_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recipient_user_id",
            "dedup_key",
            name="uq_notifications_recipient_dedup",
        ),
    )
    op.create_index(
        "ix_notifications_recipient_created",
        "notifications",
        ["recipient_user_id", "created_at"],
    )
    op.create_index(
        "ix_notifications_recipient_read",
        "notifications",
        ["recipient_user_id", "read_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notifications_recipient_read",
        table_name="notifications",
    )
    op.drop_index(
        "ix_notifications_recipient_created",
        table_name="notifications",
    )
    op.drop_table("notifications")
    op.drop_index(
        "ix_material_distributions_class_status",
        table_name="material_distributions",
    )
    op.drop_table("material_distributions")
    op.drop_index(
        "ix_material_versions_material_status",
        table_name="material_versions",
    )
    op.drop_table("material_versions")
    op.drop_index("ix_materials_academy_status", table_name="materials")
    op.drop_table("materials")
