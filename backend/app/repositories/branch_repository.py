from uuid import UUID

from sqlalchemy import func, select

from app.extensions import db
from app.models.branch import Branch
from app.models.student import Student
from app.models.teacher_branch import TeacherBranch
from app.repositories.base import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    def __init__(self) -> None:
        super().__init__(Branch)

    def get_by_id(self, branch_id: UUID) -> Branch | None:
        return db.session.scalar(
            select(Branch).where(Branch.id == branch_id)
        )

    def get_by_code(self, academy_id: UUID, code: str) -> Branch | None:
        return db.session.scalar(
            select(Branch).where(
                Branch.academy_id == academy_id,
                Branch.code == code,
            )
        )

    def list_for_academy(
        self,
        academy_id: UUID,
        *,
        include_archived: bool = False,
    ) -> list[Branch]:
        query = (
            select(Branch)
            .where(Branch.academy_id == academy_id)
            .order_by(Branch.name)
        )
        if not include_archived:
            query = query.where(Branch.status != "archived")
        return list(db.session.scalars(query))

    def list_by_ids(
        self,
        academy_id: UUID,
        branch_ids: set[UUID],
    ) -> list[Branch]:
        if not branch_ids:
            return []
        return list(
            db.session.scalars(
                select(Branch)
                .where(
                    Branch.academy_id == academy_id,
                    Branch.id.in_(branch_ids),
                    Branch.status != "archived",
                )
                .order_by(Branch.name)
            )
        )

    def active_student_count(self, academy_id: UUID, branch_id: UUID) -> int:
        return db.session.scalar(
            select(func.count(Student.id)).where(
                Student.academy_id == academy_id,
                Student.home_branch_id == branch_id,
                Student.status == "active",
            )
        ) or 0

    def active_teacher_count(self, academy_id: UUID, branch_id: UUID) -> int:
        return db.session.scalar(
            select(func.count(TeacherBranch.id)).where(
                TeacherBranch.academy_id == academy_id,
                TeacherBranch.branch_id == branch_id,
                TeacherBranch.assignment_status == "active",
            )
        ) or 0
