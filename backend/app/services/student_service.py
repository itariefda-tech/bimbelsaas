from datetime import date, datetime, timezone
from uuid import UUID

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.domain.profile_status import ProfileStatus
from app.extensions import db
from app.models.student import Student
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.cross_branch_policy import CrossBranchPolicy


class StudentService:
    def __init__(
        self,
        repository: StudentRepository | None = None,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
        user_repository: UserRepository | None = None,
        cross_branch_policy: CrossBranchPolicy | None = None,
        audit_service: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or StudentRepository()
        self.academies = academy_repository or AcademyRepository()
        self.branches = branch_repository or BranchRepository()
        self.users = user_repository or UserRepository()
        self.cross_branch = cross_branch_policy or CrossBranchPolicy()
        self.audit = audit_service or AuditLogService()

    def list_visible(self, principal: Principal, academy_id: UUID) -> list[Student]:
        if AuthorizationService.is_allowed(
            principal,
            Permission.STUDENT_VIEW,
            AuthorizationTarget(academy_id=academy_id),
        ):
            return self.repository.list_for_academy(academy_id)
        branch_ids = {
            assignment.branch_id
            for assignment in principal.assignments
            if assignment.academy_id == academy_id
            and assignment.branch_id is not None
        }
        return self.repository.list_for_branches(academy_id, branch_ids)

    def get_visible(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
    ) -> Student:
        student = self._get(academy_id, student_id)
        AuthorizationService.require(
            principal,
            Permission.STUDENT_VIEW,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=student.home_branch_id,
                student_id=student.id,
                owner_user_id=student.user_id,
            ),
        )
        return student

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        home_branch_id: UUID,
        student_code: str,
        full_name: str,
        birth_date: date | None = None,
        user_id: UUID | None = None,
    ) -> Student:
        branch = self._active_branch(academy_id, home_branch_id)
        AuthorizationService.require(
            principal,
            Permission.STUDENT_CREATE,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch.id),
        )
        code = self._normalize_code(student_code)
        if self.repository.get_by_code(academy_id, code) is not None:
            raise ConflictError(
                "A student with this code already exists in the academy.",
                "student_code_exists",
            )
        self._validate_user(user_id, academy_id)
        student = Student(
            academy_id=academy_id,
            home_branch_id=branch.id,
            user_id=user_id,
            student_code=code,
            full_name=self._required_name(full_name),
            birth_date=birth_date,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(student)
        db.session.flush()
        self._audit(
            principal,
            student,
            "student.created",
            new_data=self.serialize(student),
        )
        db.session.commit()
        return student

    def update(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
        changes: dict,
    ) -> Student:
        student = self._get(academy_id, student_id)
        AuthorizationService.require(
            principal,
            Permission.STUDENT_EDIT,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=student.home_branch_id,
                student_id=student.id,
                owner_user_id=student.user_id,
            ),
        )
        if student.status == ProfileStatus.ARCHIVED:
            raise ConflictError("Archived students cannot be edited.")
        previous = self.serialize(student)
        if "full_name" in changes:
            student.full_name = self._required_name(changes["full_name"])
        if "birth_date" in changes:
            if changes["birth_date"] is not None and not isinstance(
                changes["birth_date"],
                date,
            ):
                raise ValidationError("birth_date must be a date.")
            student.birth_date = changes["birth_date"]
        if "user_id" in changes:
            user_id = UUID(str(changes["user_id"])) if changes["user_id"] else None
            self._validate_user(user_id, academy_id)
            student.user_id = user_id
        if "home_branch_id" in changes:
            target_branch_id = UUID(str(changes["home_branch_id"]))
            self._active_branch(academy_id, target_branch_id)
            AuthorizationService.require(
                principal,
                Permission.STUDENT_EDIT,
                AuthorizationTarget(
                    academy_id=academy_id,
                    branch_id=target_branch_id,
                ),
            )
            student.home_branch_id = target_branch_id
        student.updated_by = principal.user.id
        self._audit(
            principal,
            student,
            "student.updated",
            previous_data=previous,
            new_data=self.serialize(student),
        )
        db.session.commit()
        return student

    def archive(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
    ) -> Student:
        student = self._get(academy_id, student_id)
        AuthorizationService.require(
            principal,
            Permission.STUDENT_ARCHIVE,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=student.home_branch_id,
                student_id=student.id,
            ),
        )
        if student.status != ProfileStatus.ARCHIVED:
            previous = self.serialize(student)
            student.status = ProfileStatus.ARCHIVED
            student.archived_at = datetime.now(timezone.utc)
            student.updated_by = principal.user.id
            self._audit(
                principal,
                student,
                "student.archived",
                previous_data=previous,
                new_data=self.serialize(student),
            )
            db.session.commit()
        return student

    def can_access_branch(
        self,
        academy_id: UUID,
        student_id: UUID,
        branch_id: UUID,
    ) -> bool:
        student = self._get(academy_id, student_id)
        branch = self.branches.get_by_id(branch_id)
        if (
            branch is None
            or branch.academy_id != academy_id
            or branch.status != BranchStatus.ACTIVE
        ):
            return False
        return self.cross_branch.student_can_access(student, branch_id)

    @staticmethod
    def serialize(student: Student) -> dict[str, object]:
        return {
            "id": str(student.id),
            "academy_id": str(student.academy_id),
            "home_branch_id": str(student.home_branch_id),
            "user_id": str(student.user_id) if student.user_id else None,
            "student_code": student.student_code,
            "full_name": student.full_name,
            "birth_date": (
                student.birth_date.isoformat() if student.birth_date else None
            ),
            "status": student.status,
        }

    def _get(self, academy_id: UUID, student_id: UUID) -> Student:
        student = self.repository.get_scoped(academy_id, student_id)
        if student is None:
            raise NotFoundError("Student")
        return student

    def _active_branch(self, academy_id: UUID, branch_id: UUID):
        academy = self.academies.get_by_id(academy_id)
        branch = self.branches.get_by_id(branch_id)
        if academy is None or academy.status != AcademyStatus.ACTIVE:
            raise ConflictError("Academy is not operational.")
        if (
            branch is None
            or branch.academy_id != academy_id
            or branch.status != BranchStatus.ACTIVE
        ):
            raise ValidationError(
                "Home branch must be active and belong to the academy."
            )
        return branch

    def _validate_user(self, user_id: UUID | None, academy_id: UUID) -> None:
        if user_id is None:
            return
        user = self.users.get_active_by_id(user_id)
        if user is None or user.academy_id != academy_id:
            raise ValidationError("Student user must belong to the academy.")

    @staticmethod
    def _normalize_code(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Student code is required.")
        return value.strip().upper()

    @staticmethod
    def _required_name(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Student name is required.")
        return value.strip()

    def _audit(
        self,
        principal: Principal,
        student: Student,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=student.academy_id,
                branch_id=student.home_branch_id,
                actor_user_id=principal.user.id,
                entity_type="student",
                entity_id=str(student.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
            )
        )
