from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
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


class MaterialVersion(db.Model):
    __tablename__ = "material_versions"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "version_number",
            name="uq_material_versions_number",
        ),
        UniqueConstraint(
            "id",
            "material_id",
            "academy_id",
            name="uq_material_versions_id_material_academy",
        ),
        ForeignKeyConstraint(
            ["material_id", "academy_id"],
            ["materials.id", "materials.academy_id"],
            name="fk_material_versions_material_academy",
            ondelete="CASCADE",
        ),
        Index(
            "ix_material_versions_material_status",
            "material_id",
            "status",
            "version_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    material_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    uploaded_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    material = relationship("Material", back_populates="versions")
    distributions = relationship(
        "MaterialDistribution",
        back_populates="version",
        overlaps="distributions,material",
    )
