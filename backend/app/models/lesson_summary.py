from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class LessonSummary(db.Model):
    __tablename__ = "lesson_summaries"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_lesson_summaries_session"),
        UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_lesson_summaries_id_academy_branch",
        ),
        ForeignKeyConstraint(
            ["session_id", "academy_id", "branch_id"],
            [
                "class_sessions.id",
                "class_sessions.academy_id",
                "class_sessions.branch_id",
            ],
            name="fk_lesson_summaries_session_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_lesson_summaries_teacher_academy",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_lesson_summaries_scope_status",
            "academy_id",
            "branch_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    teacher_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    lesson_topic: Mapped[str] = mapped_column(String(300), nullable=False)
    class_summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    teacher_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    homework: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    student_attention_notes: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    created_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    updated_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    published_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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

    session = relationship("ClassSession", back_populates="lesson_summary")
    edit_requests = relationship(
        "LessonSummaryEditRequest",
        back_populates="lesson_summary",
        cascade="all, delete-orphan",
    )
