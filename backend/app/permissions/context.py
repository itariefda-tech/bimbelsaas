from dataclasses import dataclass
from uuid import UUID

from app.models.auth_session import AuthSession
from app.models.role_assignment import RoleAssignment
from app.models.user import User


@dataclass(frozen=True)
class AuthorizationTarget:
    academy_id: UUID | None = None
    branch_id: UUID | None = None
    class_id: UUID | None = None
    student_id: UUID | None = None
    owner_user_id: UUID | None = None


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession
    assignments: tuple[RoleAssignment, ...]

