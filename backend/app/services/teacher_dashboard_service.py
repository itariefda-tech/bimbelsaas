from datetime import date, datetime, time, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app

from app.common.errors import NotFoundError, ValidationError
from app.domain.scheduling_status import ScheduleStatus
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.branch_repository import BranchRepository
from app.repositories.class_repository import ClassRepository
from app.repositories.material_repository import MaterialDistributionRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.authorization_service import AuthorizationService


class TeacherDashboardService:
    def __init__(
        self,
        teachers: TeacherRepository | None = None,
        schedules: ScheduleRepository | None = None,
        branches: BranchRepository | None = None,
        classes: ClassRepository | None = None,
        distributions: MaterialDistributionRepository | None = None,
        notifications: NotificationRepository | None = None,
    ) -> None:
        self.teachers = teachers or TeacherRepository()
        self.schedules = schedules or ScheduleRepository()
        self.branches = branches or BranchRepository()
        self.classes = classes or ClassRepository()
        self.distributions = distributions or MaterialDistributionRepository()
        self.notifications = notifications or NotificationRepository()

    def daily_dashboard(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        target_date: date,
        timezone_name: str,
        now: datetime | None = None,
    ) -> dict[str, object]:
        teacher = self.teachers.get_by_user(academy_id, principal.user.id)
        if teacher is None:
            raise NotFoundError("Teacher profile")
        zone = self._timezone(timezone_name)
        starts_at = datetime.combine(target_date, time.min, zone).astimezone(
            timezone.utc
        )
        ends_at = datetime.combine(
            target_date,
            time.max,
            zone,
        ).astimezone(timezone.utc)
        schedules = self.schedules.list_for_teacher_window(
            academy_id,
            teacher.id,
            starts_at,
            ends_at,
        )
        items = []
        for schedule in schedules:
            target = AuthorizationTarget(
                academy_id=schedule.academy_id,
                branch_id=schedule.branch_id,
                class_id=schedule.class_id,
            )
            AuthorizationService.require(
                principal,
                Permission.SCHEDULE_VIEW,
                target,
            )
            items.append(self._serialize_item(schedule, timezone_name))
        current = (now or datetime.now(timezone.utc)).astimezone(zone)
        next_item = next(
            (
                item
                for schedule, item in zip(schedules, items, strict=True)
                if self._as_utc(schedule.ends_at).astimezone(zone) >= current
                and schedule.status
                not in {ScheduleStatus.CANCELLED, ScheduleStatus.RESCHEDULED}
            ),
            None,
        )
        return {
            "date": target_date.isoformat(),
            "timezone": timezone_name,
            "teacher": {
                "id": str(teacher.id),
                "full_name": teacher.full_name,
            },
            "session_count": len(items),
            "notification_unread_count": self.notifications.unread_count(
                principal.user.id
            ),
            "warnings": self._warnings(schedules),
            "next_session": next_item,
            "timeline": items,
        }

    def _warnings(self, schedules) -> list[dict[str, object]]:
        active = [
            item
            for item in schedules
            if item.status
            not in {ScheduleStatus.CANCELLED, ScheduleStatus.RESCHEDULED}
        ]
        warnings = []
        workload_limit = current_app.config["TEACHER_DAILY_SESSION_WARNING"]
        if len(active) > workload_limit:
            warnings.append(
                {
                    "type": "daily_workload",
                    "severity": "medium",
                    "session_count": len(active),
                    "recommended_max": workload_limit,
                }
            )
        minimum_gap = current_app.config["TEACHER_MIN_TRANSITION_MINUTES"]
        for previous, following in zip(active, active[1:]):
            gap_minutes = int(
                (
                    self._as_utc(following.starts_at)
                    - self._as_utc(previous.ends_at)
                ).total_seconds()
                // 60
            )
            if previous.branch_id != following.branch_id and gap_minutes < minimum_gap:
                warnings.append(
                    {
                        "type": "cross_branch_transition",
                        "severity": "high",
                        "from_schedule_id": str(previous.id),
                        "to_schedule_id": str(following.id),
                        "available_minutes": gap_minutes,
                        "recommended_minutes": minimum_gap,
                    }
                )
        return warnings

    def _serialize_item(self, schedule, timezone_name: str) -> dict[str, object]:
        branch = self.branches.get_by_id(schedule.branch_id)
        academic_class = self.classes.get_scoped(
            schedule.academy_id,
            schedule.branch_id,
            schedule.class_id,
        )
        zone = ZoneInfo(timezone_name)
        session = schedule.session
        summary_status = (
            session.lesson_summary.status if session.lesson_summary else "missing"
        )
        materials = self.distributions.list_for_class(
            schedule.academy_id,
            schedule.branch_id,
            schedule.class_id,
        )
        return {
            "session_id": str(session.id),
            "schedule_id": str(schedule.id),
            "class": {
                "id": str(schedule.class_id),
                "name": academic_class.class_name,
            },
            "branch": {
                "id": str(schedule.branch_id),
                "name": branch.name,
                "timezone": branch.timezone,
            },
            "room": {
                "id": str(schedule.room_id),
                "name": schedule.room.room_name,
                "type": schedule.room.room_type,
            },
            "starts_at": self._as_utc(schedule.starts_at)
            .astimezone(zone)
            .isoformat(),
            "ends_at": self._as_utc(schedule.ends_at)
            .astimezone(zone)
            .isoformat(),
            "schedule_status": schedule.status,
            "session_status": session.status,
            "student_count": self.classes.active_enrollment_count(
                schedule.class_id
            ),
            "attendance_status": session.attendance_status,
            "lesson_summary_status": summary_status,
            "material_status": materials[0].status if materials else "missing",
            "material_count": len(materials),
            "shortcuts": {
                "attendance": (
                    f"/api/v1/branches/{schedule.branch_id}/sessions/"
                    f"{session.id}/attendance"
                ),
                "lesson_summary": (
                    f"/api/v1/branches/{schedule.branch_id}/sessions/"
                    f"{session.id}/lesson-summary"
                ),
                "materials": (
                    f"/api/v1/branches/{schedule.branch_id}/classes/"
                    f"{schedule.class_id}/materials"
                ),
            },
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
