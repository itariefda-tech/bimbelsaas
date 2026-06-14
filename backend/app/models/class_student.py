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


class ClassStudent(db.Model):
    __tablename__ = "class_students"
    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "student_id",
            name="uq_class_students_class_student",
        ),
        ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_class_students_class_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_class_students_student_academy",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_class_students_student_status",
            "academy_id",
            "student_id",
            "enrollment_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    enrollment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )
    enrolled_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    academic_class = relationship(
        "AcademicClass",
        back_populates="enrollments",
        viewonly=True,
    )
    student = relationship("Student", viewonly=True)
