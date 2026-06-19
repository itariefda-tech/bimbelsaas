from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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

    def list_active_for_academy(self, academy_id: UUID) -> list[RoleAssignment]:
        return list(
            db.session.scalars(
                select(RoleAssignment)
                .options(selectinload(RoleAssignment.user))
                .where(
                    RoleAssignment.academy_id == academy_id,
                    RoleAssignment.status == "active",
                )
                .order_by(RoleAssignment.assigned_at.desc())
            )
        )

    def get_by_id(self, assignment_id: UUID) -> RoleAssignment | None:
        return db.session.scalar(
            select(RoleAssignment)
            .options(selectinload(RoleAssignment.user))
            .where(RoleAssignment.id == assignment_id)
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
