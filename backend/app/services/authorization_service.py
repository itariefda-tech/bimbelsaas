from uuid import UUID

from sqlalchemy import select

from app.common.errors import AuthorizationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.extensions import db
from app.models.academy import Academy
from app.models.branch import Branch
from app.models.role_assignment import RoleAssignment
from app.models.subscription import AcademySubscription
from app.domain.financial_status import SubscriptionStatus
from app.permissions.constants import Permission, Role, ScopeType
from app.permissions.context import AuthorizationTarget, Principal
from app.permissions.policy import ROLE_PERMISSIONS


class AuthorizationService:
    @staticmethod
    def require(
        principal: Principal,
        permission: Permission,
        target: AuthorizationTarget,
    ) -> None:
        if not AuthorizationService.is_allowed(principal, permission, target):
            raise AuthorizationError()

    @staticmethod
    def is_allowed(
        principal: Principal,
        permission: Permission,
        target: AuthorizationTarget,
    ) -> bool:
        return any(
            AuthorizationService._assignment_allows(
                assignment,
                permission,
                target,
                principal.user.id,
            )
            for assignment in principal.assignments
        )

    @staticmethod
    def _assignment_allows(
        assignment: RoleAssignment,
        permission: Permission,
        target: AuthorizationTarget,
        user_id: UUID,
    ) -> bool:
        try:
            role = Role(assignment.role)
            scope_type = ScopeType(assignment.scope_type)
        except ValueError:
            return False

        if permission not in ROLE_PERMISSIONS.get(role, frozenset()):
            return False

        if not AuthorizationService._resource_status_allows(
            role,
            permission,
            target,
        ):
            return False

        if scope_type == ScopeType.PLATFORM:
            return True

        if target.academy_id is None or assignment.academy_id != target.academy_id:
            return False

        if permission == Permission.ACADEMY_VIEW:
            return True
        if scope_type == ScopeType.ACADEMY:
            return True
        if (
            permission == Permission.BRANCH_VIEW
            and target.branch_id is not None
            and assignment.branch_id == target.branch_id
        ):
            return True
        if scope_type == ScopeType.BRANCH:
            return (
                target.branch_id is not None
                and assignment.branch_id == target.branch_id
            )
        if scope_type == ScopeType.ASSIGNED_CLASS:
            return (
                target.class_id is not None
                and assignment.scope_id == target.class_id
                and AuthorizationService._branch_matches(assignment, target)
            )
        if scope_type == ScopeType.LINKED_STUDENT:
            return (
                target.student_id is not None
                and assignment.scope_id == target.student_id
                and AuthorizationService._branch_matches(assignment, target)
            )
        if scope_type == ScopeType.SELF:
            return target.owner_user_id == user_id
        return False

    @staticmethod
    def _resource_status_allows(
        role: Role,
        permission: Permission,
        target: AuthorizationTarget,
    ) -> bool:
        academy = (
            db.session.get(Academy, target.academy_id)
            if target.academy_id is not None
            else None
        )
        if target.academy_id is not None and academy is None:
            return False
        if (
            academy is not None
            and academy.status == AcademyStatus.ARCHIVED
            and permission
            not in {
                Permission.ACADEMY_VIEW,
                Permission.BRANCH_VIEW,
                Permission.AUDIT_LOG_VIEW,
                Permission.REPORT_VIEW,
                Permission.PLATFORM_MANAGE,
            }
        ):
            return False
        if academy is not None and role != Role.PLATFORM_OWNER:
            subscription = db.session.scalar(
                select(AcademySubscription).where(
                    AcademySubscription.academy_id == academy.id
                )
            )
            if (
                subscription is not None
                and subscription.status
                in {
                    SubscriptionStatus.SUSPENDED,
                    SubscriptionStatus.ARCHIVED,
                }
                and not AuthorizationService._is_read_permission(permission)
                and permission
                not in {
                    Permission.SUBSCRIPTION_MANAGE,
                    Permission.PAYMENT_PROOF_UPLOAD,
                }
            ):
                return False
        if (
            academy is not None
            and academy.status == AcademyStatus.SUSPENDED
            and not AuthorizationService._is_read_permission(permission)
            and role != Role.PLATFORM_OWNER
        ):
            return False

        branch = (
            db.session.get(Branch, target.branch_id)
            if target.branch_id is not None
            else None
        )
        if target.branch_id is not None:
            if branch is None or branch.academy_id != target.academy_id:
                return False
            if (
                branch.status
                in {
                    BranchStatus.INACTIVE,
                    BranchStatus.MAINTENANCE,
                    BranchStatus.SUSPENDED,
                    BranchStatus.ARCHIVED,
                }
                and not AuthorizationService._is_read_permission(permission)
                and permission
                not in {
                    Permission.BRANCH_EDIT,
                    Permission.BRANCH_ARCHIVE,
                }
            ):
                return False
        return True

    @staticmethod
    def _is_read_permission(permission: Permission) -> bool:
        return permission.value.endswith(".view")

    @staticmethod
    def _branch_matches(
        assignment: RoleAssignment,
        target: AuthorizationTarget,
    ) -> bool:
        return (
            assignment.branch_id is None
            or (
                target.branch_id is not None
                and assignment.branch_id == target.branch_id
            )
        )
