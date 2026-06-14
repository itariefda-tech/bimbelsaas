from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.organization_status import (
    BRANCH_STATUS_TRANSITIONS,
    AcademyStatus,
    BranchStatus,
)
from app.extensions import db
from app.models.branch import Branch
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService


class BranchService:
    def __init__(
        self,
        repository: BranchRepository | None = None,
        academy_repository: AcademyRepository | None = None,
        audit_service: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or BranchRepository()
        self.academies = academy_repository or AcademyRepository()
        self.audit = audit_service or AuditLogService()

    def list_visible(
        self,
        principal: Principal,
        academy_id: UUID,
    ) -> list[Branch]:
        academy = self.academies.get_by_id(academy_id)
        if academy is None:
            raise NotFoundError("Academy")
        academy_target = AuthorizationTarget(academy_id=academy_id)
        if AuthorizationService.is_allowed(
            principal,
            Permission.BRANCH_VIEW,
            academy_target,
        ):
            return self.repository.list_for_academy(academy_id)

        visible_branch_ids = {
            assignment.branch_id
            for assignment in principal.assignments
            if assignment.academy_id == academy_id
            and assignment.branch_id is not None
        }
        return self.repository.list_by_ids(academy_id, visible_branch_ids)

    def get_visible(self, principal: Principal, branch_id: UUID) -> Branch:
        branch = self._get(branch_id)
        AuthorizationService.require(
            principal,
            Permission.BRANCH_VIEW,
            self._target(branch),
        )
        return branch

    def create(
        self,
        principal: Principal,
        academy_id: UUID,
        *,
        name: str,
        code: str,
        timezone_name: str,
        address: str | None = None,
    ) -> Branch:
        academy = self.academies.get_by_id(academy_id)
        if academy is None:
            raise NotFoundError("Academy")
        if academy.status != AcademyStatus.ACTIVE:
            raise ConflictError(
                "Branches can only be created for an active academy.",
                "academy_not_operational",
            )
        AuthorizationService.require(
            principal,
            Permission.BRANCH_CREATE,
            AuthorizationTarget(academy_id=academy_id),
        )
        normalized_code = self._validate_code(code)
        if self.repository.get_by_code(academy_id, normalized_code) is not None:
            raise ConflictError(
                "A branch with this code already exists in the academy.",
                "branch_code_exists",
            )
        branch = Branch(
            academy_id=academy_id,
            name=self._required_name(name),
            code=normalized_code,
            timezone=self._validate_timezone(timezone_name),
            address=self._optional_text(address),
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(branch)
        db.session.flush()
        self._audit(principal, branch, "branch.created", new_data=self.serialize(branch))
        db.session.commit()
        return branch

    def update(
        self,
        principal: Principal,
        branch_id: UUID,
        changes: dict,
    ) -> Branch:
        branch = self._get(branch_id)
        AuthorizationService.require(
            principal,
            Permission.BRANCH_EDIT,
            self._target(branch),
        )
        if branch.status == BranchStatus.ARCHIVED:
            raise ConflictError("Archived branches cannot be edited.")

        previous = self.serialize(branch)
        if "name" in changes:
            branch.name = self._required_name(changes["name"])
        if "code" in changes:
            code = self._validate_code(changes["code"])
            existing = self.repository.get_by_code(branch.academy_id, code)
            if existing is not None and existing.id != branch.id:
                raise ConflictError(
                    "A branch with this code already exists in the academy.",
                    "branch_code_exists",
                )
            branch.code = code
        if "timezone" in changes:
            branch.timezone = self._validate_timezone(changes["timezone"])
        if "address" in changes:
            branch.address = self._optional_text(changes["address"])
        if "status" in changes and changes["status"] != branch.status:
            self._transition_status(branch, changes["status"])

        branch.updated_by = principal.user.id
        self._audit(
            principal,
            branch,
            "branch.updated",
            previous_data=previous,
            new_data=self.serialize(branch),
        )
        db.session.commit()
        return branch

    def archive(self, principal: Principal, branch_id: UUID) -> Branch:
        branch = self._get(branch_id)
        AuthorizationService.require(
            principal,
            Permission.BRANCH_ARCHIVE,
            self._target(branch),
        )
        if branch.status != BranchStatus.ARCHIVED:
            previous = self.serialize(branch)
            self._transition_status(branch, BranchStatus.ARCHIVED.value)
            branch.updated_by = principal.user.id
            self._audit(
                principal,
                branch,
                "branch.archived",
                previous_data=previous,
                new_data=self.serialize(branch),
            )
            db.session.commit()
        return branch

    def _get(self, branch_id: UUID) -> Branch:
        branch = self.repository.get_by_id(branch_id)
        if branch is None:
            raise NotFoundError("Branch")
        return branch

    @staticmethod
    def serialize(branch: Branch) -> dict[str, object]:
        return {
            "id": str(branch.id),
            "academy_id": str(branch.academy_id),
            "name": branch.name,
            "code": branch.code,
            "timezone": branch.timezone,
            "status": branch.status,
            "address": branch.address,
            "created_at": branch.created_at.isoformat(),
            "updated_at": branch.updated_at.isoformat(),
            "archived_at": (
                branch.archived_at.isoformat() if branch.archived_at else None
            ),
        }

    @staticmethod
    def _target(branch: Branch) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=branch.academy_id,
            branch_id=branch.id,
        )

    @staticmethod
    def _required_name(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Branch name is required.")
        return value.strip()

    @staticmethod
    def _validate_code(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Branch code is required.")
        code = value.strip().upper()
        if not code.replace("-", "").isalnum():
            raise ValidationError(
                "Branch code may contain letters, numbers, and hyphens."
            )
        return code

    @staticmethod
    def _validate_timezone(value: object) -> str:
        if not isinstance(value, str):
            raise ValidationError("Timezone is required.")
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValidationError("Timezone must be a valid IANA timezone.") from error
        return value

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise ValidationError("Address must be a string.")
        return value.strip()

    @staticmethod
    def _transition_status(branch: Branch, target_value: object) -> None:
        try:
            current = BranchStatus(branch.status)
            target = BranchStatus(str(target_value))
        except ValueError as error:
            raise ValidationError("Invalid branch status.") from error
        if target not in BRANCH_STATUS_TRANSITIONS[current]:
            raise ConflictError(
                f"Branch status cannot transition from {current} to {target}.",
                "invalid_status_transition",
            )
        branch.status = target.value
        branch.archived_at = (
            datetime.now(timezone.utc)
            if target == BranchStatus.ARCHIVED
            else None
        )

    def _audit(
        self,
        principal: Principal,
        branch: Branch,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=branch.academy_id,
                branch_id=branch.id,
                actor_user_id=principal.user.id,
                entity_type="branch",
                entity_id=str(branch.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
            )
        )
