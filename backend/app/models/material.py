from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Material(db.Model):
    __tablename__ = "materials"
    __table_args__ = (
        UniqueConstraint(
            "academy_id",
            "material_code",
            name="uq_materials_academy_code",
        ),
        UniqueConstraint(
            "id",
            "academy_id",
            name="uq_materials_id_academy",
        ),
        Index("ix_materials_academy_status", "academy_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(
        ForeignKey("academies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    material_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    material_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    archived_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    versions = relationship(
        "MaterialVersion",
        back_populates="material",
        cascade="all, delete-orphan",
        order_by="MaterialVersion.version_number",
    )
    distributions = relationship(
        "MaterialDistribution",
        back_populates="material",
        cascade="all, delete-orphan",
        overlaps="distributions,version",
    )
