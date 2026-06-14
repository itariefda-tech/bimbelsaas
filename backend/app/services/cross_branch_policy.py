from collections.abc import Callable
from uuid import UUID

from app.models.student import Student
from app.repositories.teacher_branch_repository import TeacherBranchRepository
from app.services.entitlement_service import EntitlementService

StudentEntitlementProvider = Callable[[UUID, UUID], bool]


class CrossBranchPolicy:
    def __init__(
        self,
        teacher_branches: TeacherBranchRepository | None = None,
        student_entitlement_provider: StudentEntitlementProvider | None = None,
    ) -> None:
        self.teacher_branches = teacher_branches or TeacherBranchRepository()
        self.student_entitlement_provider = (
            student_entitlement_provider
            or EntitlementService().student_can_access_branch
        )

    def teacher_is_assigned(self, teacher_id: UUID, branch_id: UUID) -> bool:
        assignment = self.teacher_branches.get_assignment(teacher_id, branch_id)
        return (
            assignment is not None
            and assignment.assignment_status == "active"
        )

    def student_can_access(self, student: Student, branch_id: UUID) -> bool:
        if student.home_branch_id == branch_id:
            return True
        return self.student_entitlement_provider(student.id, branch_id)
