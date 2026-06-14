from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.role_assignment import RoleAssignment
from app.repositories.base import BaseRepository


class RoleAssignmentRepository(BaseRepository[RoleAssignment]):
    def __init__(self) -> None:
        super().__init__(RoleAssignment)

    def list_active_for_user(self, user_id: UUID) -> list[RoleAssignment]:
        return list(
            db.session.scalars(
                select(RoleAssignment).where(
                    RoleAssignment.user_id == user_id,
                    RoleAssignment.status == "active",
                )
            )
        )

    def get_by_role_and_scope(
        self,
        *,
        user_id: UUID,
        role: str,
        scope_key: str,
    ) -> RoleAssignment | None:
        return db.session.scalar(
            select(RoleAssignment).where(
                RoleAssignment.user_id == user_id,
                RoleAssignment.role == role,
                RoleAssignment.scope_key == scope_key,
            )
        )
