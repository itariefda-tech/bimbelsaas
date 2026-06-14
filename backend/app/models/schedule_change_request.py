from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class ScheduleChangeRequest(db.Model):
    __tablename__ = "schedule_change_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_schedule_change_requests_schedule_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["replacement_schedule_id", "academy_id", "branch_id"],
            ["schedules.id", "schedules.academy_id", "schedules.branch_id"],
            name="fk_schedule_change_requests_replacement_scope",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_schedule_change_requests_scope_status",
            "academy_id",
            "branch_id",
            "status",
        ),
        Index(
            "ix_schedule_change_requests_schedule_status",
            "schedule_id",
            "status",
        ),
        Index(
            "uq_schedule_change_requests_one_pending",
            "schedule_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    schedule_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    replacement_schedule_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    original_class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_teacher_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_room_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    original_starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    original_ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    original_timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    original_status: Mapped[str] = mapped_column(String(30), nullable=False)

    proposed_teacher_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    proposed_room_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    proposed_starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    proposed_ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    proposed_timezone: Mapped[str] = mapped_column(String(100), nullable=False)

    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    requested_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    requester_role: Mapped[str] = mapped_column(String(50), nullable=False)
    decided_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    schedule = relationship(
        "Schedule",
        foreign_keys=[schedule_id],
        back_populates="change_requests",
    )
    replacement_schedule = relationship(
        "Schedule",
        foreign_keys=[replacement_schedule_id],
    )
