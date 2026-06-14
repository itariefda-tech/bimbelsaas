from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class AcademicClass(db.Model):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint(
            "academy_id",
            "branch_id",
            "class_code",
            name="uq_classes_branch_code",
        ),
        UniqueConstraint(
            "id",
            "academy_id",
            "branch_id",
            name="uq_classes_id_academy_branch",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_classes_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        Index("ix_classes_academy_branch_status", "academy_id", "branch_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_code: Mapped[str] = mapped_column(String(50), nullable=False)
    class_name: Mapped[str] = mapped_column(String(200), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
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

    enrollments = relationship(
        "ClassStudent",
        back_populates="academic_class",
        viewonly=True,
    )
    schedules = relationship(
        "Schedule",
        back_populates="academic_class",
        viewonly=True,
    )
