"""Create realtime outbox and notification delivery queue.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_notifications_id_academy",
        "notifications",
        ["id", "academy_id"],
    )
    op.create_table(
        "realtime_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("branch_id", UUID, nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("room", sa.String(200), nullable=False),
        sa.Column("payload", JSON, nullable=False),
        sa.Column("dedup_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedup_key", name="uq_realtime_events_dedup"),
    )
    op.create_index(
        "ix_realtime_events_status_created",
        "realtime_events",
        ["status", "created_at"],
    )
    op.create_table(
        "notification_deliveries",
        sa.Column("id", UUID, nullable=False),
        sa.Column("academy_id", UUID, nullable=False),
        sa.Column("notification_id", UUID, nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["notification_id", "academy_id"],
            ["notifications.id", "notifications.academy_id"],
            name="fk_notification_deliveries_notification_academy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "notification_id",
            "channel",
            name="uq_notification_delivery_channel",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_status_created",
        "notification_deliveries",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_deliveries_status_created",
        table_name="notification_deliveries",
    )
    op.drop_table("notification_deliveries")
    op.drop_index(
        "ix_realtime_events_status_created",
        table_name="realtime_events",
    )
    op.drop_table("realtime_events")
    op.drop_constraint(
        "uq_notifications_id_academy",
        "notifications",
        type_="unique",
    )
