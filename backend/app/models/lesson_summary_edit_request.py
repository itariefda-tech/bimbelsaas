from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, JSON, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class LessonSummaryEditRequest(db.Model):
    __tablename__ = "lesson_summary_edit_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["lesson_summary_id", "academy_id", "branch_id"],
            [
                "lesson_summaries.id",
                "lesson_summaries.academy_id",
                "lesson_summaries.branch_id",
            ],
            name="fk_lesson_summary_edit_requests_summary_scope",
            ondelete="CASCADE",
        ),
        Index(
            "ix_lesson_summary_edit_requests_scope_status",
            "academy_id",
            "branch_id",
            "status",
        ),
        Index(
            "uq_lesson_summary_edit_requests_one_pending",
            "lesson_summary_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    lesson_summary_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    proposed_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    requested_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    decided_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    lesson_summary = relationship("LessonSummary", back_populates="edit_requests")
