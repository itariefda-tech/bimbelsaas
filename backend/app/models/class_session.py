from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class ClassSession(db.Model):
    __tablename__ = "class_sessions"
    __table_args__ = (
        UniqueConstraint("schedule_id", name="uq_class_sessions_schedule"),
        UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_class_sessions_id_academy_branch",
        ),
        ForeignKeyConstraint(
            ["schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_class_sessions_schedule_scope",
            ondelete="CASCADE",
        ),
        Index(
            "ix_class_sessions_academy_branch_status",
            "academy_id",
            "branch_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="scheduled")
    attendance_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
    )
    attendance_finalized_by: Mapped[UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )
    attendance_finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    actual_ended_at: Mapped[datetime | None] = mapped_column(
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

    schedule = relationship("Schedule", back_populates="session")
    attendances = relationship(
        "Attendance",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    lesson_summary = relationship(
        "LessonSummary",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
