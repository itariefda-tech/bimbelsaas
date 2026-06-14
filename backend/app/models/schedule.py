from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Schedule(db.Model):
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_schedules_id_academy_branch",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_schedules_branch_academy",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_schedules_class_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_schedules_teacher_academy",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["room_id", "academy_id", "branch_id"],
            ["rooms.id", "rooms.academy_id", "rooms.branch_id"],
            name="fk_schedules_room_scope",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_schedules_teacher_window",
            "academy_id",
            "teacher_id",
            "starts_at",
            "ends_at",
            "status",
        ),
        Index(
            "ix_schedules_room_window",
            "academy_id",
            "branch_id",
            "room_id",
            "starts_at",
            "ends_at",
            "status",
        ),
        Index(
            "ix_schedules_class_window",
            "academy_id",
            "class_id",
            "starts_at",
            "ends_at",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    teacher_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    room_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="scheduled")
    created_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
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

    academic_class = relationship(
        "AcademicClass",
        back_populates="schedules",
        viewonly=True,
    )
    room = relationship("Room", back_populates="schedules", viewonly=True)
    teacher = relationship("Teacher", viewonly=True)
    session = relationship(
        "ClassSession",
        back_populates="schedule",
        uselist=False,
        cascade="all, delete-orphan",
    )
    change_requests = relationship(
        "ScheduleChangeRequest",
        foreign_keys="ScheduleChangeRequest.schedule_id",
        back_populates="schedule",
    )
