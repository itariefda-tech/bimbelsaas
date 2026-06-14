from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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


class Parent(db.Model):
    __tablename__ = "parents"
    __table_args__ = (
        UniqueConstraint(
            "academy_id",
            "user_id",
            name="uq_parents_academy_user",
        ),
        UniqueConstraint(
            "id",
            "academy_id",
            name="uq_parents_id_academy",
        ),
        ForeignKeyConstraint(
            ["user_id", "academy_id"],
            ["users.id", "users.academy_id"],
            name="fk_parents_user_academy",
            ondelete="CASCADE",
        ),
        Index("ix_parents_academy_status", "academy_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey("academies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    relationship_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="guardian",
    )
    primary_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )
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

    student_links = relationship(
        "ParentStudent",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
