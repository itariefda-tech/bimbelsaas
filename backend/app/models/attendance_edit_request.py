from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class AttendanceEditRequest(db.Model):
    __tablename__ = "attendance_edit_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["attendance_id", "academy_id", "branch_id"],
            ["attendances.id", "attendances.academy_id", "attendances.branch_id"],
            name="fk_attendance_edit_requests_attendance_scope",
            ondelete="CASCADE",
        ),
        Index(
            "ix_attendance_edit_requests_scope_status",
            "academy_id",
            "branch_id",
            "status",
        ),
        Index(
            "uq_attendance_edit_requests_one_pending",
            "attendance_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    attendance_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_status: Mapped[str] = mapped_column(String(30), nullable=False)
    original_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    proposed_status: Mapped[str] = mapped_column(String(30), nullable=False)
    proposed_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    attendance = relationship("Attendance", back_populates="edit_requests")
