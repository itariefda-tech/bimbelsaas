from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Teacher(db.Model):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("academy_id", "teacher_code", name="uq_teachers_academy_code"),
        UniqueConstraint("academy_id", "user_id", name="uq_teachers_academy_user"),
        UniqueConstraint("id", "academy_id", name="uq_teachers_id_academy_id"),
        ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_teachers_user_academy_users",
            ondelete="RESTRICT",
        ),
        Index("ix_teachers_academy_status", "academy_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "academies.id",
            name="fk_teachers_academy_id_academies",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    teacher_code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )
    specialization: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
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
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    branch_assignments = relationship(
        "TeacherBranch",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    user = relationship("User")
