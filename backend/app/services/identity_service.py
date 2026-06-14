from datetime import datetime, timezone
from uuid import UUID

from werkzeug.security import generate_password_hash

from app.common.errors import ConflictError, ValidationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.extensions import db
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.role_assignment import RoleAssignment
from app.models.user import User
from app.permissions.constants import Role, ScopeType
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.parent_repository import (
    ParentRepository,
    ParentStudentRepository,
)
from app.repositories.role_assignment_repository import RoleAssignmentRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditEvent, AuditLogService

ALLOWED_ROLE_SCOPES: dict[Role, frozenset[ScopeType]] = {
    Role.PLATFORM_OWNER: frozenset({ScopeType.PLATFORM}),
    Role.ACADEMY_DIRECTOR: frozenset({ScopeType.ACADEMY}),
    Role.BRANCH_MANAGER: frozenset({ScopeType.BRANCH}),
    Role.BRANCH_ADMIN: frozenset({ScopeType.BRANCH}),
    Role.TEACHER: frozenset({ScopeType.ASSIGNED_CLASS}),
    Role.PARENT: frozenset({ScopeType.LINKED_STUDENT}),
    Role.STUDENT: frozenset({ScopeType.SELF}),
}


class IdentityService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        assignment_repository: RoleAssignmentRepository | None = None,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
        audit_service: AuditLogService | None = None,
        parent_repository: ParentRepository | None = None,
        parent_student_repository: ParentStudentRepository | None = None,
        student_repository: StudentRepository | None = None,
    ) -> None:
        self.users = user_repository or UserRepository()
        self.assignments = assignment_repository or RoleAssignmentRepository()
        self.academies = academy_repository or AcademyRepository()
        self.branches = branch_repository or BranchRepository()
        self.audit = audit_service or AuditLogService()
        self.parents = parent_repository or ParentRepository()
        self.parent_students = (
            parent_student_repository or ParentStudentRepository()
        )
        self.students = student_repository or StudentRepository()

    def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        academy_id: UUID | None,
    ) -> User:
        normalized_email = email.strip().lower()
        if not normalized_email or "@" not in normalized_email:
            raise ValidationError("A valid email address is required.")
        if len(password) < 12:
            raise ValidationError("Password must contain at least 12 characters.")
        if not full_name.strip():
            raise ValidationError("Full name is required.")
        if academy_id is not None:
            academy = self.academies.get_by_id(academy_id)
            if academy is None or academy.status != AcademyStatus.ACTIVE:
                raise ValidationError(
                    "Users can only be created in an active academy."
                )
        if self.users.get_by_email(normalized_email, academy_id) is not None:
            raise ConflictError(
                "A user with this email already exists in the academy.",
                "user_already_exists",
            )

        user = User(
            academy_id=academy_id,
            identity_scope=str(academy_id) if academy_id else "platform",
            email=normalized_email,
            password_hash=generate_password_hash(password),
            full_name=full_name.strip(),
        )
        self.users.add(user)
        db.session.flush()
        return user

    def assign_role(
        self,
        *,
        user: User,
        role: Role,
        scope_type: ScopeType,
        academy_id: UUID | None = None,
        branch_id: UUID | None = None,
        scope_id: UUID | None = None,
        assigned_by: UUID | None = None,
    ) -> RoleAssignment:
        self._validate_scope(
            user=user,
            role=role,
            scope_type=scope_type,
            academy_id=academy_id,
            branch_id=branch_id,
            scope_id=scope_id,
        )
        scope_key = self._scope_key(
            scope_type=scope_type,
            academy_id=academy_id,
            branch_id=branch_id,
            scope_id=scope_id,
        )
        if (
            self.assignments.get_by_role_and_scope(
                user_id=user.id,
                role=role.value,
                scope_key=scope_key,
            )
            is not None
        ):
            raise ConflictError(
                "This role is already assigned for the requested scope.",
                "role_assignment_exists",
            )

        assignment = RoleAssignment(
            user_id=user.id,
            role=role.value,
            scope_type=scope_type.value,
            scope_key=scope_key,
            academy_id=academy_id,
            branch_id=branch_id,
            scope_id=scope_id,
            assigned_by=assigned_by,
        )
        self.assignments.add(assignment)
        db.session.flush()
        if role == Role.PARENT:
            self._activate_parent_link(
                user=user,
                academy_id=academy_id,
                student_id=scope_id,
                linked_by=assigned_by,
            )
        self.audit.record(
            AuditEvent(
                academy_id=academy_id,
                branch_id=branch_id,
                actor_user_id=assigned_by,
                entity_type="role_assignment",
                entity_id=str(assignment.id),
                action_type="role.assigned",
                new_data={
                    "user_id": str(user.id),
                    "role": role.value,
                    "scope_type": scope_type.value,
                    "scope_id": str(scope_id) if scope_id else None,
                },
            )
        )
        return assignment

    def revoke_role(
        self,
        assignment: RoleAssignment,
        *,
        revoked_by: UUID,
    ) -> None:
        assignment.status = "revoked"
        assignment.revoked_at = datetime.now(timezone.utc)
        if (
            assignment.role == Role.PARENT
            and assignment.academy_id is not None
            and assignment.scope_id is not None
        ):
            parent = self.parents.get_by_user(
                assignment.academy_id,
                assignment.user_id,
            )
            if parent is not None:
                link = self.parent_students.get_link(
                    assignment.academy_id,
                    parent.id,
                    assignment.scope_id,
                )
                if link is not None:
                    link.relationship_status = "inactive"
                    link.unlinked_at = datetime.now(timezone.utc)
        self.audit.record(
            AuditEvent(
                academy_id=assignment.academy_id,
                branch_id=assignment.branch_id,
                actor_user_id=revoked_by,
                entity_type="role_assignment",
                entity_id=str(assignment.id),
                action_type="role.revoked",
                previous_data={"status": "active"},
                new_data={"status": "revoked"},
            )
        )

    @staticmethod
    def _scope_key(
        *,
        scope_type: ScopeType,
        academy_id: UUID | None,
        branch_id: UUID | None,
        scope_id: UUID | None,
    ) -> str:
        values = {
            ScopeType.PLATFORM: "platform",
            ScopeType.ACADEMY: str(academy_id),
            ScopeType.BRANCH: str(branch_id),
            ScopeType.ASSIGNED_CLASS: str(scope_id),
            ScopeType.LINKED_STUDENT: str(scope_id),
            ScopeType.SELF: "self",
        }
        return f"{scope_type.value}:{values[scope_type]}"

    def _validate_scope(
        self,
        *,
        user: User,
        role: Role,
        scope_type: ScopeType,
        academy_id: UUID | None,
        branch_id: UUID | None,
        scope_id: UUID | None,
    ) -> None:
        if scope_type not in ALLOWED_ROLE_SCOPES[role]:
            raise ValidationError(
                f"{role.value} cannot be assigned with {scope_type.value} scope."
            )
        if role == Role.PLATFORM_OWNER:
            if scope_type != ScopeType.PLATFORM or any(
                value is not None for value in (academy_id, branch_id, scope_id)
            ):
                raise ValidationError(
                    "Platform owner must use platform scope without tenant IDs."
                )
            return

        if academy_id is None or user.academy_id != academy_id:
            raise ValidationError(
                "Role assignment academy must match the user academy."
            )
        academy = self.academies.get_by_id(academy_id)
        if academy is None or academy.status != AcademyStatus.ACTIVE:
            raise ValidationError(
                "Roles can only be assigned in an active academy."
            )
        if branch_id is not None:
            branch = self.branches.get_by_id(branch_id)
            if (
                branch is None
                or branch.academy_id != academy_id
                or branch.status != BranchStatus.ACTIVE
            ):
                raise ValidationError(
                    "Role assignment branch must be active and belong to the academy."
                )
        if scope_type == ScopeType.ACADEMY:
            if branch_id is not None or scope_id is not None:
                raise ValidationError("Academy scope cannot include branch or entity IDs.")
            return
        if scope_type == ScopeType.BRANCH:
            if branch_id is None or scope_id is not None:
                raise ValidationError(
                    "Branch scope requires branch_id and no entity scope_id."
                )
            return
        if scope_type in {ScopeType.ASSIGNED_CLASS, ScopeType.LINKED_STUDENT}:
            if scope_id is None:
                raise ValidationError("Entity-scoped roles require scope_id.")
            if scope_type == ScopeType.LINKED_STUDENT:
                student = self.students.get_scoped(academy_id, scope_id)
                if student is None or student.status != "active":
                    raise ValidationError(
                        "Linked student must be active and belong to the academy."
                    )
                if branch_id is not None and branch_id != student.home_branch_id:
                    raise ValidationError(
                        "Linked student branch must match the home branch."
                    )
            return
        if scope_type == ScopeType.SELF:
            if scope_id is not None:
                raise ValidationError("Self scope cannot include scope_id.")
            return
        raise ValidationError("Unsupported role assignment scope.")

    def _activate_parent_link(
        self,
        *,
        user: User,
        academy_id: UUID | None,
        student_id: UUID | None,
        linked_by: UUID | None,
    ) -> None:
        if academy_id is None or student_id is None:
            raise ValidationError("Parent links require academy and student IDs.")
        parent = self.parents.get_by_user(academy_id, user.id)
        if parent is None:
            parent = Parent(
                academy_id=academy_id,
                user_id=user.id,
                relationship_type="guardian",
                primary_contact=True,
            )
            self.parents.add(parent)
            db.session.flush()
        else:
            parent.status = "active"
        link = self.parent_students.get_link(
            academy_id,
            parent.id,
            student_id,
        )
        if link is None:
            self.parent_students.add(
                ParentStudent(
                    academy_id=academy_id,
                    parent_id=parent.id,
                    student_id=student_id,
                    linked_by=linked_by,
                )
            )
        else:
            link.relationship_status = "active"
            link.linked_by = linked_by
            link.linked_at = datetime.now(timezone.utc)
            link.unlinked_at = None
