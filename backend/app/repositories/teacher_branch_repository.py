from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.teacher_branch import TeacherBranch
from app.repositories.base import BaseRepository


class TeacherBranchRepository(BaseRepository[TeacherBranch]):
    def __init__(self) -> None:
        super().__init__(TeacherBranch)

    def get_assignment(
        self,
        teacher_id: UUID,
        branch_id: UUID,
    ) -> TeacherBranch | None:
        return db.session.scalar(
            select(TeacherBranch).where(
                TeacherBranch.teacher_id == teacher_id,
                TeacherBranch.branch_id == branch_id,
            )
        )

    def list_active_for_teacher(self, teacher_id: UUID) -> list[TeacherBranch]:
        return list(
            db.session.scalars(
                select(TeacherBranch).where(
                    TeacherBranch.teacher_id == teacher_id,
                    TeacherBranch.assignment_status == "active",
                )
            )
        )

    def teacher_ids_for_branches(
        self,
        academy_id: UUID,
        branch_ids: set[UUID],
    ) -> set[UUID]:
        if not branch_ids:
            return set()
        return set(
            db.session.scalars(
                select(TeacherBranch.teacher_id).where(
                    TeacherBranch.academy_id == academy_id,
                    TeacherBranch.branch_id.in_(branch_ids),
                    TeacherBranch.assignment_status == "active",
                )
            )
        )

