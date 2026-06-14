from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["recipient_user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_notifications_recipient_academy",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "recipient_user_id",
            "dedup_key",
            name="uq_notifications_recipient_dedup",
        ),
        Index(
            "ix_notifications_recipient_created",
            "recipient_user_id",
            "created_at",
        ),
        Index(
            "ix_notifications_recipient_read",
            "recipient_user_id",
            "read_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    recipient_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
