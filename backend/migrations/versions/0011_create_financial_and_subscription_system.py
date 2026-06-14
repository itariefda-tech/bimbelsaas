"""Create academic billing, subscriptions, addons, and entitlements.

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "saas_plans",
        sa.Column("id", UUID, nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("billing_interval", sa.String(30), nullable=False),
        sa.Column("features", JSON, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "addon_definitions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "academy_subscriptions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("plan_id", UUID, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grace_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["academy_id"], ["academies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["saas_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academy_id", name="uq_subscriptions_academy"),
    )
    op.create_index(
        "ix_subscriptions_status_period",
        "academy_subscriptions",
        ["status", "current_period_end"],
    )
    op.create_table(
        "academic_invoices",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("invoice_number", sa.String(80), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("paid_minor", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_invoices_branch_academy",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_invoices_student_academy",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academy_id", "invoice_number", name="uq_invoices_academy_number"),
        sa.UniqueConstraint("id", "academy_id", "branch_id", name="uq_invoices_id_scope"),
    )
    op.create_index(
        "ix_invoices_student_status",
        "academic_invoices",
        ["academy_id", "student_id", "status"],
    )
    op.create_index(
        "ix_invoices_branch_due",
        "academic_invoices",
        ["academy_id", "branch_id", "due_date"],
    )
    op.create_table(
        "academic_payments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("invoice_id", UUID, nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("proof_storage_key", sa.String(500), nullable=True),
        sa.Column("proof_file_name", sa.String(255), nullable=True),
        sa.Column("proof_mime_type", sa.String(150), nullable=True),
        sa.Column("proof_checksum_sha256", sa.String(64), nullable=True),
        sa.Column("submitted_by", UUID, nullable=False),
        sa.Column("confirmed_by", UUID, nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["invoice_id", "academy_id", "branch_id"],
            ["academic_invoices.id", "academic_invoices.academy_id", "academic_invoices.branch_id"],
            name="fk_payments_invoice_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academy_id", "reference_number", name="uq_payments_academy_reference"),
    )
    op.create_index(
        "ix_payments_invoice_status",
        "academic_payments",
        ["invoice_id", "status"],
    )
    op.create_table(
        "student_addons",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("addon_id", UUID, nullable=False),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("purchased_by", UUID, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["addon_id"], ["addon_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_student_addons_student_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_addons_feature_status",
        "student_addons",
        ["student_id", "feature_key", "status"],
    )
    op.create_table(
        "student_branch_access",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("student_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("student_addon_id", UUID, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_addon_id"], ["student_addons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_student_branch_access_student_academy",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_student_branch_access_branch_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "branch_id", name="uq_student_branch_access"),
    )


def downgrade() -> None:
    op.drop_table("student_branch_access")
    op.drop_index("ix_student_addons_feature_status", table_name="student_addons")
    op.drop_table("student_addons")
    op.drop_index("ix_payments_invoice_status", table_name="academic_payments")
    op.drop_table("academic_payments")
    op.drop_index("ix_invoices_branch_due", table_name="academic_invoices")
    op.drop_index("ix_invoices_student_status", table_name="academic_invoices")
    op.drop_table("academic_invoices")
    op.drop_index("ix_subscriptions_status_period", table_name="academy_subscriptions")
    op.drop_table("academy_subscriptions")
    op.drop_table("addon_definitions")
    op.drop_table("saas_plans")
