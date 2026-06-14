from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import NotFoundError, ValidationError
from app.domain.material_status import NotificationPriority
from app.extensions import db
from app.models.notification import Notification
from app.permissions.context import Principal
from app.repositories.notification_repository import NotificationRepository
from app.services.realtime_service import NotificationDeliveryService


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository | None = None,
    ) -> None:
        self.repository = repository or NotificationRepository()

    def emit(
        self,
        *,
        academy_id: UUID,
        recipient_user_id: UUID,
        notification_type: str,
        priority: str,
        title: str,
        payload: dict,
        dedup_key: str,
    ) -> Notification:
        existing = self.repository.get_by_dedup(recipient_user_id, dedup_key)
        if existing is not None:
            return existing
        notification = Notification(
            academy_id=academy_id,
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            priority=self._priority(priority),
            title=title,
            payload=payload,
            dedup_key=dedup_key,
        )
        self.repository.add(notification)
        db.session.flush()
        NotificationDeliveryService().enqueue(notification.id, academy_id)
        return notification

    def list_for_principal(
        self,
        principal: Principal,
        *,
        limit: int,
        unread_only: bool,
    ) -> dict[str, object]:
        bounded_limit = min(max(limit, 1), 50)
        items = self.repository.list_for_recipient(
            principal.user.id,
            limit=bounded_limit,
            unread_only=unread_only,
        )
        return {
            "unread_count": self.repository.unread_count(principal.user.id),
            "items": [self.serialize(item) for item in items],
        }

    def mark_read(
        self,
        principal: Principal,
        notification_id: UUID,
    ) -> Notification:
        notification = self.repository.get_for_recipient(
            notification_id,
            principal.user.id,
        )
        if notification is None:
            raise NotFoundError("Notification")
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            db.session.commit()
        return notification

    @staticmethod
    def serialize(notification: Notification) -> dict[str, object]:
        return {
            "id": str(notification.id),
            "type": notification.notification_type,
            "priority": notification.priority,
            "title": notification.title,
            "payload": notification.payload,
            "read_at": (
                notification.read_at.isoformat()
                if notification.read_at
                else None
            ),
            "created_at": notification.created_at.isoformat(),
        }

    @staticmethod
    def _priority(value: str) -> NotificationPriority:
        try:
            return NotificationPriority(value)
        except ValueError as error:
            raise ValidationError("Invalid notification priority.") from error
