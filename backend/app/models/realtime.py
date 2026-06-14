from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class RealtimeEvent(db.Model):
    __tablename__ = "realtime_events"
    __table_args__ = (
        UniqueConstraint("dedup_key", name="uq_realtime_events_dedup"),
        Index("ix_realtime_events_status_created", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    room: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationDelivery(db.Model):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("notification_id", "channel", name="uq_notification_delivery_channel"),
        ForeignKeyConstraint(
            ["notification_id", "academy_id"],
            ["notifications.id", "notifications.academy_id"],
            name="fk_notification_deliveries_notification_academy",
            ondelete="CASCADE",
        ),
        Index("ix_notification_deliveries_status_created", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    notification_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
