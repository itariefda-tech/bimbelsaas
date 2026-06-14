from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.common.errors import AuthorizationError, NotFoundError, ValidationError
from app.extensions import db
from app.models.branch import Branch
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.notification_repository import NotificationRepository
from app.repositories.parent_repository import (
    ParentRepository,
    ParentStudentRepository,
)
from app.services.authorization_service import AuthorizationService


class ParentExperienceService:
    def __init__(
        self,
        parents: ParentRepository | None = None,
        links: ParentStudentRepository | None = None,
        notifications: NotificationRepository | None = None,
    ) -> None:
        self.parents = parents or ParentRepository()
        self.links = links or ParentStudentRepository()
        self.notifications = notifications or NotificationRepository()

    def dashboard(
        self,
        principal: Principal,
        academy_id: UUID,
    ) -> dict[str, object]:
        parent = self._parent(principal, academy_id)
        children = self.list_children(principal, academy_id)
        return {
            "parent": {
                "id": str(parent.id),
                "user_id": str(principal.user.id),
                "full_name": principal.user.full_name,
            },
            "linked_child_count": len(children),
            "notification_unread_count": self.notifications.unread_count(
                principal.user.id
            ),
            "children": children,
        }

    def list_children(
        self,
        principal: Principal,
        academy_id: UUID,
    ) -> list[dict[str, object]]:
        parent = self._parent(principal, academy_id)
        items = []
        for link in self.links.list_active_for_parent(academy_id, parent.id):
            student = link.student
            AuthorizationService.require(
                principal,
                Permission.STUDENT_VIEW,
                self._target(student),
            )
            items.append(self._child_card(student))
        return items

    def overview(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
    ) -> dict[str, object]:
        student = self._linked_student(principal, academy_id, student_id)
        classes = self.links.active_classes(academy_id, student_id)
        teachers = self.links.active_teachers(
            academy_id,
            {item.id for item in classes},
        )
        counts = self.links.attendance_counts(academy_id, student_id)
        total = sum(counts.values())
        attended = sum(
            counts.get(status, 0)
            for status in ("present", "late", "online")
        )
        return {
            "student": self._child_card(student),
            "active_classes": [
                {
                    "id": str(item.id),
                    "name": item.class_name,
                    "branch_id": str(item.branch_id),
                }
                for item in classes
            ],
            "active_teachers": [
                {
                    "id": str(item.id),
                    "full_name": item.full_name,
                    "specialization": item.specialization,
                }
                for item in teachers
            ],
            "attendance": {
                "total_finalized_sessions": total,
                "attended_sessions": attended,
                "percentage": (
                    round((attended / total) * 100, 1) if total else None
                ),
                "by_status": counts,
            },
            "shortcuts": self._shortcuts(student.id),
        }

    def attendance_history(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        self._linked_student(principal, academy_id, student_id)
        return [
            {
                "id": str(attendance.id),
                "session_id": str(attendance.session_id),
                "attendance_status": attendance.attendance_status,
                "note": attendance.note,
                "class": {
                    "id": str(academic_class.id),
                    "name": academic_class.class_name,
                },
                "branch": {
                    "id": str(branch.id),
                    "name": branch.name,
                },
                "starts_at": self._iso(schedule.starts_at),
                "ends_at": self._iso(schedule.ends_at),
                "finalized_at": (
                    self._iso(attendance.session.attendance_finalized_at)
                    if attendance.session.attendance_finalized_at
                    else None
                ),
            }
            for attendance, schedule, academic_class, branch
            in self.links.attendance_history(academy_id, student_id, limit)
        ]

    def published_summaries(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        self._linked_student(principal, academy_id, student_id)
        return [
            {
                "id": str(summary.id),
                "session_id": str(summary.session_id),
                "lesson_topic": summary.lesson_topic,
                "class_summary": summary.class_summary,
                "teacher_notes": summary.teacher_notes,
                "homework": summary.homework,
                "published_at": (
                    self._iso(summary.published_at)
                    if summary.published_at
                    else None
                ),
                "class": {
                    "id": str(academic_class.id),
                    "name": academic_class.class_name,
                },
                "branch": {
                    "id": str(branch.id),
                    "name": branch.name,
                },
                "session_starts_at": self._iso(schedule.starts_at),
            }
            for summary, schedule, academic_class, branch
            in self.links.published_summaries(academy_id, student_id, limit)
        ]

    def schedule_overview(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        timezone_name: str,
    ) -> dict[str, object]:
        self._linked_student(principal, academy_id, student_id)
        if starts_at >= ends_at:
            raise ValidationError("from must be earlier than to.")
        zone = self._timezone(timezone_name)
        schedules = self.links.schedule_window(
            academy_id,
            student_id,
            starts_at,
            ends_at,
        )
        branch_ids = {item.branch_id for item in schedules}
        branches = (
            {
                branch.id: branch
                for branch in db.session.query(Branch).filter(
                    Branch.id.in_(branch_ids)
                )
            }
            if branch_ids
            else {}
        )
        return {
            "from": self._iso(starts_at),
            "to": self._iso(ends_at),
            "timezone": timezone_name,
            "items": [
                {
                    "schedule_id": str(item.id),
                    "session_id": (
                        str(item.session.id) if item.session else None
                    ),
                    "class": {
                        "id": str(item.class_id),
                        "name": item.academic_class.class_name,
                    },
                    "branch": {
                        "id": str(item.branch_id),
                        "name": branches[item.branch_id].name,
                    },
                    "teacher": {
                        "id": str(item.teacher_id),
                        "full_name": item.teacher.full_name,
                    },
                    "room": {
                        "id": str(item.room_id),
                        "name": item.room.room_name,
                    },
                    "starts_at": self._as_utc(item.starts_at)
                    .astimezone(zone)
                    .isoformat(),
                    "ends_at": self._as_utc(item.ends_at)
                    .astimezone(zone)
                    .isoformat(),
                    "status": item.status,
                }
                for item in schedules
            ],
        }

    def _parent(self, principal: Principal, academy_id: UUID):
        if principal.user.academy_id != academy_id:
            raise AuthorizationError()
        parent = self.parents.get_by_user(academy_id, principal.user.id)
        if parent is None or parent.status != "active":
            raise NotFoundError("Parent profile")
        return parent

    def _linked_student(
        self,
        principal: Principal,
        academy_id: UUID,
        student_id: UUID,
    ):
        parent = self._parent(principal, academy_id)
        link = self.links.active_link(academy_id, parent.id, student_id)
        if link is None:
            raise AuthorizationError()
        AuthorizationService.require(
            principal,
            Permission.STUDENT_VIEW,
            self._target(link.student),
        )
        return link.student

    @staticmethod
    def _target(student) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=student.academy_id,
            branch_id=student.home_branch_id,
            student_id=student.id,
            owner_user_id=student.user_id,
        )

    @staticmethod
    def _child_card(student) -> dict[str, object]:
        return {
            "id": str(student.id),
            "student_code": student.student_code,
            "full_name": student.full_name,
            "birth_date": (
                student.birth_date.isoformat() if student.birth_date else None
            ),
            "status": student.status,
            "home_branch_id": str(student.home_branch_id),
            "shortcuts": ParentExperienceService._shortcuts(student.id),
        }

    @staticmethod
    def _shortcuts(student_id: UUID) -> dict[str, str]:
        base = f"/api/v1/parent/children/{student_id}"
        return {
            "overview": f"{base}/overview",
            "attendance": f"{base}/attendance",
            "lesson_summaries": f"{base}/lesson-summaries",
            "schedule": f"{base}/schedule",
        }

    @staticmethod
    def _timezone(value: str) -> ZoneInfo:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValidationError("Invalid IANA timezone.") from error

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _iso(value: datetime) -> str:
        return ParentExperienceService._as_utc(value).isoformat()
