from uuid import UUID

from sqlalchemy import func, select

from app.extensions import db
from app.models.material import Material
from app.models.material_distribution import MaterialDistribution
from app.models.material_version import MaterialVersion
from app.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    def __init__(self) -> None:
        super().__init__(Material)

    def get_scoped(self, academy_id: UUID, material_id: UUID) -> Material | None:
        return db.session.scalar(
            select(Material).where(
                Material.id == material_id,
                Material.academy_id == academy_id,
            )
        )

    def get_by_code(self, academy_id: UUID, code: str) -> Material | None:
        return db.session.scalar(
            select(Material).where(
                Material.academy_id == academy_id,
                Material.material_code == code,
            )
        )

    def list_for_academy(self, academy_id: UUID) -> list[Material]:
        return list(
            db.session.scalars(
                select(Material)
                .where(Material.academy_id == academy_id)
                .order_by(Material.title, Material.id)
            )
        )


class MaterialVersionRepository(BaseRepository[MaterialVersion]):
    def __init__(self) -> None:
        super().__init__(MaterialVersion)

    def get_scoped(
        self,
        academy_id: UUID,
        material_id: UUID,
        version_id: UUID,
    ) -> MaterialVersion | None:
        return db.session.scalar(
            select(MaterialVersion).where(
                MaterialVersion.id == version_id,
                MaterialVersion.academy_id == academy_id,
                MaterialVersion.material_id == material_id,
            )
        )

    def next_version_number(self, material_id: UUID) -> int:
        latest = db.session.scalar(
            select(func.max(MaterialVersion.version_number)).where(
                MaterialVersion.material_id == material_id
            )
        )
        return int(latest or 0) + 1


class MaterialDistributionRepository(BaseRepository[MaterialDistribution]):
    def __init__(self) -> None:
        super().__init__(MaterialDistribution)

    def get_target(
        self,
        material_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> MaterialDistribution | None:
        return db.session.scalar(
            select(MaterialDistribution).where(
                MaterialDistribution.material_id == material_id,
                MaterialDistribution.branch_id == branch_id,
                MaterialDistribution.class_id == class_id,
            )
        )

    def list_for_class(
        self,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> list[MaterialDistribution]:
        return list(
            db.session.scalars(
                select(MaterialDistribution)
                .where(
                    MaterialDistribution.academy_id == academy_id,
                    MaterialDistribution.branch_id == branch_id,
                    MaterialDistribution.class_id == class_id,
                    MaterialDistribution.status.in_(["ready", "updated"]),
                )
                .order_by(MaterialDistribution.updated_at.desc())
            )
        )
