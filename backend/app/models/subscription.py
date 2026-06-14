from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class SaasPlan(db.Model):
    __tablename__ = "saas_plans"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="IDR")
    billing_interval: Mapped[str] = mapped_column(String(30), nullable=False, default="monthly")
    features: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class AcademySubscription(db.Model):
    __tablename__ = "academy_subscriptions"
    __table_args__ = (
        UniqueConstraint("academy_id", name="uq_subscriptions_academy"),
        Index("ix_subscriptions_status_period", "status", "current_period_end"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey("academies.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("saas_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="trial")
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grace_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
