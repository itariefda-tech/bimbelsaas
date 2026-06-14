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


class ParentStudent(db.Model):
    __tablename__ = "parent_students"
    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "student_id",
            name="uq_parent_students_parent_student",
        ),
        ForeignKeyConstraint(
            ["parent_id", "academy_id"],
            ["parents.id", "parents.academy_id"],
            name="fk_parent_students_parent_academy",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_parent_students_student_academy",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_parent_students_parent_status",
            "academy_id",
            "parent_id",
            "relationship_status",
        ),
        Index(
            "ix_parent_students_student_status",
            "academy_id",
            "student_id",
            "relationship_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    parent_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    relationship_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )
    linked_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    unlinked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    parent = relationship("Parent", back_populates="student_links")
    student = relationship("Student", viewonly=True)
