from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, ForeignKeyConstraint, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class BetaAcademyOnboarding(db.Model):
    __tablename__ = "beta_academy_onboardings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_beta_onboardings_academy",
            ondelete="CASCADE",
        ),
        Index("ix_beta_onboardings_status", "status", "target_start_date"),
        Index("ix_beta_onboardings_academy_status", "academy_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    cohort_label: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="invited")
    operational_owner_name: Mapped[str] = mapped_column(String(200), nullable=False)
    operational_owner_contact: Mapped[str] = mapped_column(String(200), nullable=False)
    success_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    target_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    updated_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BetaFeedback(db.Model):
    __tablename__ = "beta_feedback"
    __table_args__ = (
        ForeignKeyConstraint(
            ["academy_id"],
            ["academies.id"],
            name="fk_beta_feedback_academy",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_beta_feedback_branch_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reporter_user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_beta_feedback_reporter_academy",
            ondelete="RESTRICT",
        ),
        Index("ix_beta_feedback_academy_status", "academy_id", "status"),
        Index("ix_beta_feedback_branch_status", "branch_id", "status"),
        Index("ix_beta_feedback_severity_created", "severity", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    reporter_user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    source_role: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
