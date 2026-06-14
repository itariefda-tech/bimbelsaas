from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.student import Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self) -> None:
        super().__init__(Student)

    def get_scoped(self, academy_id: UUID, student_id: UUID) -> Student | None:
        return db.session.scalar(
            select(Student).where(
                Student.id == student_id,
                Student.academy_id == academy_id,
            )
        )

    def get_by_code(self, academy_id: UUID, student_code: str) -> Student | None:
        return db.session.scalar(
            select(Student).where(
                Student.academy_id == academy_id,
                Student.student_code == student_code,
            )
        )

    def list_for_academy(self, academy_id: UUID) -> list[Student]:
        return list(
            db.session.scalars(
                select(Student)
                .where(
                    Student.academy_id == academy_id,
                    Student.status != "archived",
                )
                .order_by(Student.full_name)
            )
        )

    def list_for_branches(
        self,
        academy_id: UUID,
        branch_ids: set[UUID],
    ) -> list[Student]:
        if not branch_ids:
            return []
        return list(
            db.session.scalars(
                select(Student)
                .where(
                    Student.academy_id == academy_id,
                    Student.home_branch_id.in_(branch_ids),
                    Student.status != "archived",
                )
                .order_by(Student.full_name)
            )
        )

