from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.extensions import db, socketio
from app.models.notification import Notification
from app.models.realtime import NotificationDelivery, RealtimeEvent


class RealtimeService:
    def enqueue(
        self,
        *,
        academy_id: UUID,
        event_type: str,
        payload: dict,
        dedup_key: str,
        branch_id: UUID | None = None,
        room: str | None = None,
    ) -> RealtimeEvent:
        existing = db.session.scalar(
            select(RealtimeEvent).where(RealtimeEvent.dedup_key == dedup_key)
        )
        if existing is not None:
            return existing
        event = RealtimeEvent(
            academy_id=academy_id,
            branch_id=branch_id,
            event_type=event_type,
            room=room or f"academy:{academy_id}",
            payload=payload,
            dedup_key=dedup_key,
        )
        db.session.add(event)
        db.session.flush()
        return event

    def process(self, limit: int = 100) -> dict[str, int]:
        delivered = failed = 0
        events = list(
            db.session.scalars(
                select(RealtimeEvent)
                .where(RealtimeEvent.status.in_(("queued", "failed")))
                .order_by(RealtimeEvent.created_at)
                .limit(min(max(limit, 1), 500))
            )
        )
        for event in events:
            event.attempts += 1
            try:
                socketio.emit(event.event_type, event.payload, to=event.room)
                event.status = "delivered"
                event.delivered_at = datetime.now(timezone.utc)
                event.last_error = None
                delivered += 1
            except Exception as error:
                event.status = "failed"
                event.last_error = str(error)[:500]
                failed += 1
        db.session.commit()
        return {"processed": len(events), "delivered": delivered, "failed": failed}


class NotificationDeliveryService:
    def enqueue(self, notification_id: UUID, academy_id: UUID) -> NotificationDelivery:
        existing = db.session.scalar(
            select(NotificationDelivery).where(
                NotificationDelivery.notification_id == notification_id,
                NotificationDelivery.channel == "in_app",
            )
        )
        if existing is not None:
            return existing
        delivery = NotificationDelivery(
            academy_id=academy_id,
            notification_id=notification_id,
            channel="in_app",
        )
        db.session.add(delivery)
        db.session.flush()
        return delivery

    def process(self, limit: int = 100) -> dict[str, int]:
        delivered = failed = 0
        deliveries = list(
            db.session.scalars(
                select(NotificationDelivery)
                .where(NotificationDelivery.status.in_(("queued", "failed")))
                .order_by(NotificationDelivery.created_at)
                .limit(min(max(limit, 1), 500))
            )
        )
        realtime = RealtimeService()
        for delivery in deliveries:
            delivery.attempts += 1
            notification = db.session.get(Notification, delivery.notification_id)
            if notification is None:
                delivery.status = "failed"
                delivery.last_error = "Notification no longer exists."
                failed += 1
                continue
            realtime.enqueue(
                academy_id=delivery.academy_id,
                event_type="notification.created",
                payload={"notification_id": str(notification.id)},
                dedup_key=f"notification-delivery:{delivery.id}",
                room=f"user:{notification.recipient_user_id}",
            )
            delivery.status = "delivered"
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.last_error = None
            delivered += 1
        db.session.commit()
        return {
            "processed": len(deliveries),
            "delivered": delivered,
            "failed": failed,
        }
