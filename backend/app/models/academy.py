from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Academy(db.Model):
    __tablename__ = "academies"
    __table_args__ = (Index("ix_academies_status", "status"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Asia/Jakarta",
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="IDR")
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

    branches = relationship(
        "Branch",
        back_populates="academy",
        cascade="all, delete-orphan",
    )
    users = relationship("User", back_populates="academy")

