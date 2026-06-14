from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.domain.profile_status import ProfileStatus, TeacherBranchStatus
from app.extensions import db
from app.models.teacher import Teacher
from app.models.teacher_branch import TeacherBranch
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.teacher_branch_repository import TeacherBranchRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService


class TeacherService:
    def __init__(
        self,
        repository: TeacherRepository | None = None,
        assignment_repository: TeacherBranchRepository | None = None,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
        user_repository: UserRepository | None = None,
        audit_service: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or TeacherRepository()
        self.assignments = assignment_repository or TeacherBranchRepository()
        self.academies = academy_repository or AcademyRepository()
        self.branches = branch_repository or BranchRepository()
        self.users = user_repository or UserRepository()
        self.audit = audit_service or AuditLogService()

    def list_visible(self, principal: Principal, academy_id: UUID) -> list[Teacher]:
        if AuthorizationService.is_allowed(
            principal,
            Permission.TEACHER_VIEW,
            AuthorizationTarget(academy_id=academy_id),
        ):
            return self.repository.list_for_academy(academy_id)
        branch_ids = self._visible_branch_ids(principal, academy_id)
        teacher_ids = self.assignments.teacher_ids_for_branches(
            academy_id,
            branch_ids,
        )
        return self.repository.list_by_ids(academy_id, teacher_ids)

    def get_visible(
        self,
        principal: Principal,
        academy_id: UUID,
        teacher_id: UUID,
    ) -> Teacher:
        teacher = self._get(academy_id, teacher_id)
        if AuthorizationService.is_allowed(
            principal,
            Permission.TEACHER_VIEW,
            AuthorizationTarget(academy_id=academy_id),
        ):
            return teacher
        visible_branches = self._visible_branch_ids(principal, academy_id)
        if not any(
            assignment.assignment_status == TeacherBranchStatus.ACTIVE
            and assignment.branch_id in visible_branches
            for assignment in teacher.branch_assignments
        ):
            from app.common.errors import AuthorizationError

            raise AuthorizationError()
        return teacher

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        initial_branch_id: UUID,
        teacher_code: str,
        full_name: str,
        employment_status: str = "active",
        specialization: str | None = None,
        user_id: UUID | None = None,
    ) -> Teacher:
        branch = self._active_branch(academy_id, initial_branch_id)
        AuthorizationService.require(
            principal,
            Permission.TEACHER_CREATE,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch.id),
        )
        code = self._normalize_code(teacher_code)
        if self.repository.get_by_code(academy_id, code) is not None:
            raise ConflictError(
                "A teacher with this code already exists in the academy.",
                "teacher_code_exists",
            )
        self._validate_user(user_id, academy_id)
        teacher = Teacher(
            academy_id=academy_id,
            user_id=user_id,
            teacher_code=code,
            full_name=self._required_name(full_name),
            employment_status=self._required_status(employment_status),
            specialization=self._optional_text(specialization),
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(teacher)
        db.session.flush()
        self._assign(principal, teacher, branch.id)
        self._audit(
            principal,
            teacher,
            "teacher.created",
            new_data=self.serialize(teacher),
        )
        db.session.commit()
        return teacher

    def update(
        self,
        principal: Principal,
        academy_id: UUID,
        teacher_id: UUID,
        changes: dict,
    ) -> Teacher:
        teacher = self._get(academy_id, teacher_id)
        self._require_teacher_edit(principal, teacher)
        if teacher.status == ProfileStatus.ARCHIVED:
            raise ConflictError("Archived teachers cannot be edited.")
        previous = self.serialize(teacher)
        if "full_name" in changes:
            teacher.full_name = self._required_name(changes["full_name"])
        if "employment_status" in changes:
            teacher.employment_status = self._required_status(
                changes["employment_status"]
            )
        if "specialization" in changes:
            teacher.specialization = self._optional_text(
                changes["specialization"]
            )
        if "user_id" in changes:
            user_id = UUID(str(changes["user_id"])) if changes["user_id"] else None
            self._validate_user(user_id, academy_id)
            teacher.user_id = user_id
        teacher.updated_by = principal.user.id
        self._audit(
            principal,
            teacher,
            "teacher.updated",
            previous_data=previous,
            new_data=self.serialize(teacher),
        )
        db.session.commit()
        return teacher

    def assign_branch(
        self,
        principal: Principal,
        academy_id: UUID,
        teacher_id: UUID,
        branch_id: UUID,
    ) -> TeacherBranch:
        teacher = self._get(academy_id, teacher_id)
        branch = self._active_branch(academy_id, branch_id)
        AuthorizationService.require(
            principal,
            Permission.TEACHER_EDIT,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch.id),
        )
        existing = self.assignments.get_assignment(teacher.id, branch.id)
        if existing is not None:
            if existing.assignment_status == TeacherBranchStatus.ACTIVE:
                raise ConflictError(
                    "Teacher is already assigned to this branch.",
                    "teacher_branch_exists",
                )
            existing.assignment_status = TeacherBranchStatus.ACTIVE
            existing.assigned_by = principal.user.id
            existing.assigned_at = datetime.now(timezone.utc)
            existing.ended_at = None
            assignment = existing
        else:
            assignment = self._assign(principal, teacher, branch.id)
        self._audit_assignment(principal, teacher, assignment, "teacher.branch_assigned")
        db.session.commit()
        return assignment

    def archive(
        self,
        principal: Principal,
        academy_id: UUID,
        teacher_id: UUID,
    ) -> Teacher:
        teacher = self._get(academy_id, teacher_id)
        self._require_teacher_edit(principal, teacher)
        if teacher.status != ProfileStatus.ARCHIVED:
            previous = self.serialize(teacher)
            teacher.status = ProfileStatus.ARCHIVED
            teacher.archived_at = datetime.now(timezone.utc)
            teacher.updated_by = principal.user.id
            for assignment in teacher.branch_assignments:
                if assignment.assignment_status == TeacherBranchStatus.ACTIVE:
                    assignment.assignment_status = TeacherBranchStatus.ENDED
                    assignment.ended_at = datetime.now(timezone.utc)
            self._audit(
                principal,
                teacher,
                "teacher.archived",
                previous_data=previous,
                new_data=self.serialize(teacher),
            )
            db.session.commit()
        return teacher

    def remove_branch(
        self,
        principal: Principal,
        academy_id: UUID,
        teacher_id: UUID,
        branch_id: UUID,
    ) -> TeacherBranch:
        teacher = self._get(academy_id, teacher_id)
        assignment = self.assignments.get_assignment(teacher.id, branch_id)
        if assignment is None or assignment.assignment_status != TeacherBranchStatus.ACTIVE:
            raise NotFoundError("Teacher branch assignment")
        AuthorizationService.require(
            principal,
            Permission.TEACHER_EDIT,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        active_assignments = self.assignments.list_active_for_teacher(teacher.id)
        if len(active_assignments) <= 1:
            raise ConflictError(
                "A teacher must remain assigned to at least one active branch.",
                "teacher_requires_branch",
            )
        assignment.assignment_status = TeacherBranchStatus.ENDED
        assignment.ended_at = datetime.now(timezone.utc)
        self._audit_assignment(principal, teacher, assignment, "teacher.branch_removed")
        db.session.commit()
        return assignment

    @staticmethod
    def serialize(teacher: Teacher) -> dict[str, object]:
        return {
            "id": str(teacher.id),
            "academy_id": str(teacher.academy_id),
            "user_id": str(teacher.user_id) if teacher.user_id else None,
            "teacher_code": teacher.teacher_code,
            "full_name": teacher.full_name,
            "employment_status": teacher.employment_status,
            "specialization": teacher.specialization,
            "status": teacher.status,
            "branch_ids": sorted(
                str(assignment.branch_id)
                for assignment in teacher.branch_assignments
                if assignment.assignment_status == TeacherBranchStatus.ACTIVE
            ),
        }

    def _assign(
        self,
        principal: Principal,
        teacher: Teacher,
        branch_id: UUID,
    ) -> TeacherBranch:
        assignment = TeacherBranch(
            academy_id=teacher.academy_id,
            teacher_id=teacher.id,
            branch_id=branch_id,
            assigned_by=principal.user.id,
        )
        self.assignments.add(assignment)
        db.session.flush()
        return assignment

    def _get(self, academy_id: UUID, teacher_id: UUID) -> Teacher:
        teacher = self.repository.get_scoped(academy_id, teacher_id)
        if teacher is None:
            raise NotFoundError("Teacher")
        return teacher

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
                "Branch must be active and belong to the academy."
            )
        return branch

    def _require_teacher_edit(self, principal: Principal, teacher: Teacher) -> None:
        active = [
            item
            for item in teacher.branch_assignments
            if item.assignment_status == TeacherBranchStatus.ACTIVE
        ]
        if not any(
            AuthorizationService.is_allowed(
                principal,
                Permission.TEACHER_EDIT,
                AuthorizationTarget(
                    academy_id=teacher.academy_id,
                    branch_id=item.branch_id,
                ),
            )
            for item in active
        ):
            from app.common.errors import AuthorizationError

            raise AuthorizationError()

    def _validate_user(self, user_id: UUID | None, academy_id: UUID) -> None:
        if user_id is None:
            return
        user = self.users.get_active_by_id(user_id)
        if user is None or user.academy_id != academy_id:
            raise ValidationError("Teacher user must belong to the academy.")

    @staticmethod
    def _visible_branch_ids(principal: Principal, academy_id: UUID) -> set[UUID]:
        return {
            assignment.branch_id
            for assignment in principal.assignments
            if assignment.academy_id == academy_id
            and assignment.branch_id is not None
        }

    @staticmethod
    def _normalize_code(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Teacher code is required.")
        return value.strip().upper()

    @staticmethod
    def _required_name(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Teacher name is required.")
        return value.strip()

    @staticmethod
    def _required_status(value: object) -> str:
        if value not in {"active", "inactive", "contract", "leave"}:
            raise ValidationError("Invalid teacher employment status.")
        return str(value)

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise ValidationError("Specialization must be a string.")
        return value.strip()

    def _audit(
        self,
        principal: Principal,
        teacher: Teacher,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=teacher.academy_id,
                actor_user_id=principal.user.id,
                entity_type="teacher",
                entity_id=str(teacher.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
            )
        )

    def _audit_assignment(
        self,
        principal: Principal,
        teacher: Teacher,
        assignment: TeacherBranch,
        action: str,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=teacher.academy_id,
                branch_id=assignment.branch_id,
                actor_user_id=principal.user.id,
                entity_type="teacher_branch",
                entity_id=str(assignment.id),
                action_type=action,
                new_data={
                    "teacher_id": str(teacher.id),
                    "branch_id": str(assignment.branch_id),
                    "status": assignment.assignment_status,
                },
            )
        )
