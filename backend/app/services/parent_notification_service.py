from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.class_student import ClassStudent
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.services.notification_service import NotificationService
from app.services.realtime_service import RealtimeService


class ParentNotificationService:
    def emit_for_class(
        self,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        notification_type: str,
        priority: str,
        title: str,
        payload: dict,
        dedup_key: str,
    ) -> int:
        rows = db.session.execute(
            select(Parent.user_id, ParentStudent.student_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .join(ClassStudent, ClassStudent.student_id == ParentStudent.student_id)
            .where(
                Parent.academy_id == academy_id,
                Parent.status == "active",
                ParentStudent.relationship_status == "active",
                ClassStudent.class_id == class_id,
                ClassStudent.enrollment_status == "active",
            )
        ).all()
        for user_id, student_id in rows:
            NotificationService().emit(
                academy_id=academy_id,
                recipient_user_id=user_id,
                notification_type=notification_type,
                priority=priority,
                title=title,
                payload={**payload, "student_id": str(student_id)},
                dedup_key=f"{dedup_key}:{student_id}",
            )
            RealtimeService().enqueue(
                academy_id=academy_id,
                branch_id=branch_id,
                event_type=notification_type,
                payload={**payload, "student_id": str(student_id)},
                dedup_key=f"realtime:{dedup_key}:{student_id}",
                room=f"student:{student_id}",
            )
        return len(rows)
