from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.scheduling_status import (
    SCHEDULE_TRANSITIONS,
    SESSION_STATUS_FOR_SCHEDULE,
    ScheduleStatus,
)
from app.extensions import db
from app.models.class_session import ClassSession
from app.models.schedule import Schedule
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.schedule_repository import (
    ClassSessionRepository,
    ScheduleRepository,
)
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.schedule_validation_service import (
    ScheduleCandidate,
    ScheduleValidationService,
)


class ScheduleService:
    def __init__(
        self,
        repository: ScheduleRepository | None = None,
        sessions: ClassSessionRepository | None = None,
        validator: ScheduleValidationService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or ScheduleRepository()
        self.sessions = sessions or ClassSessionRepository()
        self.validator = validator or ScheduleValidationService()
        self.audit = audit or AuditLogService()

    def list_for_branch(
        self,
        principal: Principal,
        academy_id: UUID,
        branch_id: UUID,
    ) -> list[Schedule]:
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_VIEW,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        return self.repository.list_for_branch(academy_id, branch_id)

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        teacher_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        timezone_name: str,
        status: str = ScheduleStatus.SCHEDULED,
    ) -> Schedule:
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_CREATE,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=branch_id,
                class_id=class_id,
            ),
        )
        schedule_status = self._creation_status(status)
        timezone_name = self._timezone(timezone_name)
        self.validator.validate(
            ScheduleCandidate(
                academy_id=academy_id,
                branch_id=branch_id,
                class_id=class_id,
                teacher_id=teacher_id,
                room_id=room_id,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        )
        schedule = Schedule(
            academy_id=academy_id,
            branch_id=branch_id,
            class_id=class_id,
            teacher_id=teacher_id,
            room_id=room_id,
            starts_at=starts_at,
            ends_at=ends_at,
            timezone=timezone_name,
            status=schedule_status,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(schedule)
        db.session.flush()
        session = ClassSession(
            academy_id=academy_id,
            branch_id=branch_id,
            schedule_id=schedule.id,
            status=SESSION_STATUS_FOR_SCHEDULE[schedule_status],
        )
        self.sessions.add(session)
        db.session.flush()
        self._audit(
            principal,
            schedule,
            "schedule.created",
            new_data=self.serialize(schedule),
        )
        db.session.commit()
        return schedule

    def transition(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
        target_status: str,
        reason: str | None = None,
    ) -> Schedule:
        schedule = self._get(academy_id, branch_id, schedule_id)
        target = self._status(target_status)
        permission = (
            Permission.SCHEDULE_CANCEL
            if target == ScheduleStatus.CANCELLED
            else Permission.SCHEDULE_EDIT
        )
        AuthorizationService.require(
            principal,
            permission,
            AuthorizationTarget(
                academy_id=academy_id,
                branch_id=branch_id,
                class_id=schedule.class_id,
            ),
        )
        current = self._status(schedule.status)
        if target not in SCHEDULE_TRANSITIONS[current]:
            raise ConflictError(
                f"Schedule cannot transition from {current} to {target}.",
                "invalid_schedule_transition",
            )
        previous = self.serialize(schedule)
        schedule.status = target
        schedule.updated_by = principal.user.id
        schedule.session.status = SESSION_STATUS_FOR_SCHEDULE[target]
        self._audit(
            principal,
            schedule,
            "schedule.status_changed",
            previous_data=previous,
            new_data=self.serialize(schedule),
            reason=reason,
        )
        db.session.commit()
        return schedule

    def _get(
        self,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
    ) -> Schedule:
        schedule = self.repository.get_scoped(academy_id, branch_id, schedule_id)
        if schedule is None:
            raise NotFoundError("Schedule")
        return schedule

    @staticmethod
    def serialize(schedule: Schedule) -> dict[str, object]:
        return {
            "id": str(schedule.id),
            "academy_id": str(schedule.academy_id),
            "branch_id": str(schedule.branch_id),
            "class_id": str(schedule.class_id),
            "teacher_id": str(schedule.teacher_id),
            "room_id": str(schedule.room_id),
            "starts_at": schedule.starts_at.isoformat(),
            "ends_at": schedule.ends_at.isoformat(),
            "timezone": schedule.timezone,
            "status": schedule.status,
            "session": {
                "id": str(schedule.session.id),
                "status": schedule.session.status,
            }
            if schedule.session
            else None,
        }

    @staticmethod
    def _creation_status(value: str) -> ScheduleStatus:
        status = ScheduleService._status(value)
        if status not in {ScheduleStatus.DRAFT, ScheduleStatus.SCHEDULED}:
            raise ValidationError("New schedules must start as draft or scheduled.")
        return status

    @staticmethod
    def _status(value: str) -> ScheduleStatus:
        try:
            return ScheduleStatus(value)
        except ValueError as error:
            raise ValidationError("Invalid schedule status.") from error

    @staticmethod
    def _timezone(value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValidationError("Invalid IANA timezone.") from error
        return value

    def _audit(
        self,
        principal: Principal,
        schedule: Schedule,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
        reason: str | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=schedule.academy_id,
                branch_id=schedule.branch_id,
                actor_user_id=principal.user.id,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )
