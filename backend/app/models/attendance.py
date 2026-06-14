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


class Attendance(db.Model):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="uq_attendances_session_student",
        ),
        UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_attendances_id_academy_branch",
        ),
        ForeignKeyConstraint(
            ["session_id", "academy_id", "branch_id"],
            [
                "class_sessions.id",
                "class_sessions.academy_id",
                "class_sessions.branch_id",
            ],
            name="fk_attendances_session_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_attendances_student_academy",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_attendances_scope_session",
            "academy_id",
            "branch_id",
            "session_id",
        ),
        Index(
            "ix_attendances_student_recorded",
            "academy_id",
            "student_id",
            "recorded_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    attendance_status: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recorded_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    updated_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
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

    session = relationship("ClassSession", back_populates="attendances")
    edit_requests = relationship(
        "AttendanceEditRequest",
        back_populates="attendance",
        cascade="all, delete-orphan",
    )
