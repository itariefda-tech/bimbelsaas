from uuid import UUID

from app.common.errors import NotFoundError
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.branch_repository import BranchRepository
from app.services.authorization_service import AuthorizationService


class BranchAnalyticsService:
    def __init__(self, repository: BranchRepository | None = None) -> None:
        self.repository = repository or BranchRepository()

    def summary(self, principal: Principal, branch_id: UUID) -> dict[str, object]:
        branch = self.repository.get_by_id(branch_id)
        if branch is None:
            raise NotFoundError("Branch")
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(
                academy_id=branch.academy_id,
                branch_id=branch.id,
            ),
        )
        return {
            "academy_id": str(branch.academy_id),
            "branch_id": str(branch.id),
            "active_students": self.repository.active_student_count(
                branch.academy_id,
                branch.id,
            ),
            "active_teachers": self.repository.active_teacher_count(
                branch.academy_id,
                branch.id,
            ),
        }

