from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.academy import Academy
from app.repositories.base import BaseRepository


class AcademyRepository(BaseRepository[Academy]):
    def __init__(self) -> None:
        super().__init__(Academy)

    def get_by_id(self, academy_id: UUID) -> Academy | None:
        return db.session.scalar(
            select(Academy).where(Academy.id == academy_id)
        )

    def get_by_slug(self, slug: str) -> Academy | None:
        return db.session.scalar(
            select(Academy).where(Academy.slug == slug)
        )

    def list_all(self, *, include_archived: bool = False) -> list[Academy]:
        query = select(Academy).order_by(Academy.name)
        if not include_archived:
            query = query.where(Academy.status != "archived")
        return list(db.session.scalars(query))

    def list_by_ids(self, academy_ids: set[UUID]) -> list[Academy]:
        if not academy_ids:
            return []
        return list(
            db.session.scalars(
                select(Academy)
                .where(
                    Academy.id.in_(academy_ids),
                    Academy.status != "archived",
                )
                .order_by(Academy.name)
            )
        )

