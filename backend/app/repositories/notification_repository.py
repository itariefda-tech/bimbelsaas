from uuid import UUID

from sqlalchemy import func, select

from app.extensions import db
from app.models.notification import Notification
from app.models.role_assignment import RoleAssignment
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self) -> None:
        super().__init__(Notification)

    def get_by_dedup(
        self,
        recipient_user_id: UUID,
        dedup_key: str,
    ) -> Notification | None:
        return db.session.scalar(
            select(Notification).where(
                Notification.recipient_user_id == recipient_user_id,
                Notification.dedup_key == dedup_key,
            )
        )

    def get_for_recipient(
        self,
        notification_id: UUID,
        recipient_user_id: UUID,
    ) -> Notification | None:
        return db.session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_user_id == recipient_user_id,
            )
        )

    def list_for_recipient(
        self,
        recipient_user_id: UUID,
        *,
        limit: int,
        unread_only: bool,
    ) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.recipient_user_id == recipient_user_id)
            .order_by(Notification.created_at.desc(), Notification.id)
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
        return list(db.session.scalars(query))

    def unread_count(self, recipient_user_id: UUID) -> int:
        return int(
            db.session.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.recipient_user_id == recipient_user_id,
                    Notification.read_at.is_(None),
                )
            )
            or 0
        )

    def teacher_user_ids_for_class(
        self,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> set[UUID]:
        return set(
            db.session.scalars(
                select(RoleAssignment.user_id).where(
                    RoleAssignment.academy_id == academy_id,
                    RoleAssignment.branch_id == branch_id,
                    RoleAssignment.scope_id == class_id,
                    RoleAssignment.role == "teacher",
                    RoleAssignment.scope_type == "assigned_class",
                    RoleAssignment.status == "active",
                )
            )
        )
