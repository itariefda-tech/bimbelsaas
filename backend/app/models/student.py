from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("academy_id", "student_code", name="uq_students_academy_code"),
        UniqueConstraint("academy_id", "user_id", name="uq_students_academy_user"),
        UniqueConstraint("id", "academy_id", name="uq_students_id_academy_id"),
        ForeignKeyConstraint(
            ["home_branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_students_home_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_students_user_academy_users",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_students_academy_home_branch_status",
            "academy_id",
            "home_branch_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "academies.id",
            name="fk_students_academy_id_academies",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    home_branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    student_code: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
