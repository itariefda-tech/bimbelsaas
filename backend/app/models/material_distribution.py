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


class MaterialDistribution(db.Model):
    __tablename__ = "material_distributions"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "branch_id",
            "class_id",
            name="uq_material_distributions_target",
        ),
        ForeignKeyConstraint(
            ["material_id", "academy_id"],
            ["materials.id", "materials.academy_id"],
            name="fk_material_distributions_material_academy",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["version_id", "material_id", "academy_id"],
            [
                "material_versions.id",
                "material_versions.material_id",
                "material_versions.academy_id",
            ],
            name="fk_material_distributions_version_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_material_distributions_branch_academy",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["class_id", "academy_id", "branch_id"],
            ["classes.id", "classes.academy_id", "classes.branch_id"],
            name="fk_material_distributions_class_scope",
            ondelete="CASCADE",
        ),
        Index(
            "ix_material_distributions_class_status",
            "academy_id",
            "branch_id",
            "class_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    material_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ready")
    distributed_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    distributed_at: Mapped[datetime] = mapped_column(
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

    material = relationship(
        "Material",
        back_populates="distributions",
        overlaps="distributions,version",
    )
    version = relationship(
        "MaterialVersion",
        back_populates="distributions",
        overlaps="distributions,material",
    )
