from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self) -> None:
        super().__init__(Teacher)

    def get_scoped(self, academy_id: UUID, teacher_id: UUID) -> Teacher | None:
        return db.session.scalar(
            select(Teacher)
            .options(selectinload(Teacher.branch_assignments), selectinload(Teacher.user))
            .where(
                Teacher.id == teacher_id,
                Teacher.academy_id == academy_id,
            )
        )

    def get_by_user(self, academy_id: UUID, user_id: UUID) -> Teacher | None:
        return db.session.scalar(
            select(Teacher)
            .options(selectinload(Teacher.branch_assignments), selectinload(Teacher.user))
            .where(
                Teacher.academy_id == academy_id,
                Teacher.user_id == user_id,
                Teacher.status == "active",
            )
        )

    def get_by_code(self, academy_id: UUID, teacher_code: str) -> Teacher | None:
        return db.session.scalar(
            select(Teacher).where(
                Teacher.academy_id == academy_id,
                Teacher.teacher_code == teacher_code,
            )
        )

    def list_for_academy(self, academy_id: UUID) -> list[Teacher]:
        return list(
            db.session.scalars(
                select(Teacher)
                .options(selectinload(Teacher.branch_assignments), selectinload(Teacher.user))
                .where(
                    Teacher.academy_id == academy_id,
                    Teacher.status != "archived",
                )
                .order_by(Teacher.full_name)
            )
        )

    def list_by_ids(
        self,
        academy_id: UUID,
        teacher_ids: set[UUID],
    ) -> list[Teacher]:
        if not teacher_ids:
            return []
        return list(
            db.session.scalars(
                select(Teacher)
                .options(selectinload(Teacher.branch_assignments), selectinload(Teacher.user))
                .where(
                    Teacher.academy_id == academy_id,
                    Teacher.id.in_(teacher_ids),
                    Teacher.status != "archived",
                )
                .order_by(Teacher.full_name)
            )
        )
