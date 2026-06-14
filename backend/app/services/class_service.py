from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.profile_status import ProfileStatus
from app.domain.scheduling_status import ClassStatus, EnrollmentStatus
from app.extensions import db
from app.models.academic_class import AcademicClass
from app.models.class_student import ClassStudent
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.branch_repository import BranchRepository
from app.repositories.class_repository import ClassRepository, ClassStudentRepository
from app.repositories.student_repository import StudentRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.cross_branch_policy import CrossBranchPolicy


class ClassService:
    def __init__(
        self,
        repository: ClassRepository | None = None,
        enrollments: ClassStudentRepository | None = None,
        students: StudentRepository | None = None,
        branches: BranchRepository | None = None,
        cross_branch: CrossBranchPolicy | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or ClassRepository()
        self.enrollments = enrollments or ClassStudentRepository()
        self.students = students or StudentRepository()
        self.branches = branches or BranchRepository()
        self.cross_branch = cross_branch or CrossBranchPolicy()
        self.audit = audit or AuditLogService()

    def list_for_branch(
        self,
        principal: Principal,
        academy_id: UUID,
        branch_id: UUID,
    ) -> list[AcademicClass]:
        AuthorizationService.require(
            principal,
            Permission.CLASS_VIEW,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        return self.repository.list_for_branch(academy_id, branch_id)

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_code: str,
        class_name: str,
        capacity: int,
    ) -> AcademicClass:
        AuthorizationService.require(
            principal,
            Permission.CLASS_MANAGE,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        branch = self.branches.get_by_id(branch_id)
        if branch is None or branch.academy_id != academy_id or branch.status != "active":
            raise ValidationError("Class branch must be active and belong to the academy.")
        code = self._required_text(class_code, "Class code").upper()
        if self.repository.get_by_code(academy_id, branch_id, code):
            raise ConflictError(
                "A class with this code already exists in the branch.",
                "class_code_exists",
            )
        academic_class = AcademicClass(
            academy_id=academy_id,
            branch_id=branch_id,
            class_code=code,
            class_name=self._required_text(class_name, "Class name"),
            capacity=capacity,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(academic_class)
        db.session.flush()
        self._audit(principal, academic_class, "class.created")
        db.session.commit()
        return academic_class

    def enroll_student(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        student_id: UUID,
    ) -> ClassStudent:
        AuthorizationService.require(
            principal,
            Permission.CLASS_MANAGE,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=branch_id,
                class_id=class_id,
            ),
        )
        academic_class = self._active_class(academy_id, branch_id, class_id)
        student = self.students.get_scoped(academy_id, student_id)
        if student is None or student.status != ProfileStatus.ACTIVE:
            raise ValidationError("Student must be active and belong to the academy.")
        if not self.cross_branch.student_can_access(student, branch_id):
            raise ConflictError(
                "Student does not have access to the class branch.",
                "student_cross_branch_denied",
            )
        existing = self.enrollments.get_enrollment(class_id, student_id)
        if existing and existing.enrollment_status == EnrollmentStatus.ACTIVE:
            raise ConflictError(
                "Student is already enrolled in this class.",
                "student_already_enrolled",
            )
        if self.repository.active_enrollment_count(class_id) >= academic_class.capacity:
            raise ConflictError("Class capacity has been reached.", "class_capacity_reached")
        if existing:
            existing.enrollment_status = EnrollmentStatus.ACTIVE
            existing.enrolled_by = principal.user.id
            existing.joined_at = datetime.now(timezone.utc)
            existing.ended_at = None
            enrollment = existing
        else:
            enrollment = ClassStudent(
                academy_id=academy_id,
                branch_id=branch_id,
                class_id=class_id,
                student_id=student_id,
                enrolled_by=principal.user.id,
            )
            self.enrollments.add(enrollment)
        db.session.flush()
        self.audit.record(
            AuditEvent(
                academy_id=academy_id,
                branch_id=branch_id,
                actor_user_id=principal.user.id,
                entity_type="class_student",
                entity_id=str(enrollment.id),
                action_type="class.student_enrolled",
                new_data={
                    "class_id": str(class_id),
                    "student_id": str(student_id),
                },
            )
        )
        db.session.commit()
        return enrollment

    def _active_class(
        self,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> AcademicClass:
        academic_class = self.repository.get_scoped(academy_id, branch_id, class_id)
        if academic_class is None:
            raise NotFoundError("Class")
        if academic_class.status != ClassStatus.ACTIVE:
            raise ConflictError("Class is not active.", "class_not_active")
        return academic_class

    @staticmethod
    def serialize(academic_class: AcademicClass) -> dict[str, object]:
        return {
            "id": str(academic_class.id),
            "academy_id": str(academic_class.academy_id),
            "branch_id": str(academic_class.branch_id),
            "class_code": academic_class.class_code,
            "class_name": academic_class.class_name,
            "capacity": academic_class.capacity,
            "status": academic_class.status,
            "active_student_ids": sorted(
                str(item.student_id)
                for item in academic_class.enrollments
                if item.enrollment_status == EnrollmentStatus.ACTIVE
            ),
        }

    @staticmethod
    def _required_text(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label} is required.")
        return value.strip()

    def _audit(
        self,
        principal: Principal,
        academic_class: AcademicClass,
        action: str,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=academic_class.academy_id,
                branch_id=academic_class.branch_id,
                actor_user_id=principal.user.id,
                entity_type="class",
                entity_id=str(academic_class.id),
                action_type=action,
                new_data=self.serialize(academic_class),
            )
        )
