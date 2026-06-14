from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Branch(db.Model):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("academy_id", "code", name="uq_branches_academy_code"),
        UniqueConstraint("id", "academy_id", name="uq_branches_id_academy_id"),
        Index("ix_branches_academy_status", "academy_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "academies.id",
            name="fk_branches_academy_id_academies",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Asia/Jakarta",
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    address: Mapped[str | None] = mapped_column(String(1000), nullable=True)
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

    academy = relationship("Academy", back_populates="branches")
