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


class TeacherBranch(db.Model):
    __tablename__ = "teacher_branches"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "branch_id",
            name="uq_teacher_branches_teacher_branch",
        ),
        ForeignKeyConstraint(
            ["teacher_id", "academy_id"],
            ["teachers.id", "teachers.academy_id"],
            name="fk_teacher_branches_teacher_academy_teachers",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_teacher_branches_branch_academy_branches",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_teacher_branches_academy_branch_status",
            "academy_id",
            "branch_id",
            "assignment_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    teacher_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    assignment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )
    assigned_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    teacher = relationship("Teacher", back_populates="branch_assignments")

