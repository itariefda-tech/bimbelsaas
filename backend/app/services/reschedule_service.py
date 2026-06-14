from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import AuthorizationError, ConflictError, NotFoundError
from app.domain.scheduling_status import (
    RescheduleRequestStatus,
    SESSION_STATUS_FOR_SCHEDULE,
    ScheduleStatus,
)
from app.extensions import db
from app.models.class_session import ClassSession
from app.models.schedule import Schedule
from app.models.schedule_change_request import ScheduleChangeRequest
from app.permissions.constants import Permission, Role
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.schedule_repository import (
    ClassSessionRepository,
    ScheduleChangeRequestRepository,
    ScheduleRepository,
)
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.schedule_service import ScheduleService
from app.services.schedule_validation_service import (
    ScheduleCandidate,
    ScheduleValidationService,
)


class RescheduleService:
    _requester_role_priority = (
        Role.PLATFORM_OWNER,
        Role.ACADEMY_DIRECTOR,
        Role.BRANCH_MANAGER,
        Role.BRANCH_ADMIN,
        Role.TEACHER,
        Role.PARENT,
        Role.STUDENT,
    )
    _approvers = {
        Role.PLATFORM_OWNER: {Role.PLATFORM_OWNER},
        Role.ACADEMY_DIRECTOR: {Role.PLATFORM_OWNER, Role.ACADEMY_DIRECTOR},
        Role.BRANCH_MANAGER: {
            Role.PLATFORM_OWNER,
            Role.ACADEMY_DIRECTOR,
            Role.BRANCH_MANAGER,
        },
        Role.BRANCH_ADMIN: {
            Role.PLATFORM_OWNER,
            Role.ACADEMY_DIRECTOR,
            Role.BRANCH_MANAGER,
        },
        Role.TEACHER: {
            Role.PLATFORM_OWNER,
            Role.ACADEMY_DIRECTOR,
            Role.BRANCH_MANAGER,
            Role.BRANCH_ADMIN,
        },
        Role.PARENT: {
            Role.PLATFORM_OWNER,
            Role.ACADEMY_DIRECTOR,
            Role.BRANCH_MANAGER,
            Role.BRANCH_ADMIN,
        },
        Role.STUDENT: {
            Role.PLATFORM_OWNER,
            Role.ACADEMY_DIRECTOR,
            Role.BRANCH_MANAGER,
            Role.BRANCH_ADMIN,
        },
    }

    def __init__(
        self,
        schedules: ScheduleRepository | None = None,
        requests: ScheduleChangeRequestRepository | None = None,
        sessions: ClassSessionRepository | None = None,
        validator: ScheduleValidationService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.schedules = schedules or ScheduleRepository()
        self.requests = requests or ScheduleChangeRequestRepository()
        self.sessions = sessions or ClassSessionRepository()
        self.validator = validator or ScheduleValidationService()
        self.audit = audit or AuditLogService()

    def list_for_schedule(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
    ) -> list[ScheduleChangeRequest]:
        schedule = self._schedule(academy_id, branch_id, schedule_id)
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_VIEW,
            self._target(schedule),
        )
        return self.requests.list_for_schedule(academy_id, branch_id, schedule_id)

    def request(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
        teacher_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        timezone_name: str,
        reason: str,
    ) -> ScheduleChangeRequest:
        schedule = self._schedule(academy_id, branch_id, schedule_id)
        target = self._target(schedule)
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_REQUEST_RESCHEDULE,
            target,
        )
        if schedule.status in {
            ScheduleStatus.COMPLETED,
            ScheduleStatus.CANCELLED,
            ScheduleStatus.RESCHEDULED,
        }:
            raise ConflictError(
                "This schedule can no longer be rescheduled.",
                "schedule_not_reschedulable",
            )
        if self.requests.pending_for_schedule(academy_id, branch_id, schedule_id):
            raise ConflictError(
                "A pending reschedule request already exists.",
                "pending_reschedule_exists",
            )

        timezone_name = ScheduleService._timezone(timezone_name)
        if (
            teacher_id == schedule.teacher_id
            and room_id == schedule.room_id
            and starts_at == schedule.starts_at
            and ends_at == schedule.ends_at
            and timezone_name == schedule.timezone
        ):
            raise ConflictError(
                "The proposed schedule is unchanged.",
                "reschedule_has_no_changes",
            )
        self.validator.validate(
            self._candidate(
                schedule,
                teacher_id,
                room_id,
                starts_at,
                ends_at,
            )
        )
        requester_role = self._requester_role(principal, target)
        change = ScheduleChangeRequest(
            academy_id=academy_id,
            branch_id=branch_id,
            schedule_id=schedule.id,
            original_class_id=schedule.class_id,
            original_teacher_id=schedule.teacher_id,
            original_room_id=schedule.room_id,
            original_starts_at=schedule.starts_at,
            original_ends_at=schedule.ends_at,
            original_timezone=schedule.timezone,
            original_status=schedule.status,
            proposed_teacher_id=teacher_id,
            proposed_room_id=room_id,
            proposed_starts_at=starts_at,
            proposed_ends_at=ends_at,
            proposed_timezone=timezone_name,
            reason=reason,
            requested_by=principal.user.id,
            requester_role=requester_role,
        )
        self.requests.add(change)
        db.session.flush()
        self._audit(
            principal,
            change,
            "schedule.reschedule_requested",
            new_data=self.serialize(change),
            reason=reason,
        )
        db.session.commit()
        return change

    def approve(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
        decision_reason: str,
    ) -> ScheduleChangeRequest:
        change = self._request(academy_id, branch_id, request_id, for_update=True)
        schedule = self._schedule(academy_id, branch_id, change.schedule_id)
        self._require_approver(principal, change, schedule)
        self._require_pending(change)
        self._require_unchanged_original(change, schedule)

        self.validator.validate(
            self._candidate(
                schedule,
                change.proposed_teacher_id,
                change.proposed_room_id,
                change.proposed_starts_at,
                change.proposed_ends_at,
            )
        )

        previous_schedule = ScheduleService.serialize(schedule)
        replacement = Schedule(
            academy_id=schedule.academy_id,
            branch_id=schedule.branch_id,
            class_id=schedule.class_id,
            teacher_id=change.proposed_teacher_id,
            room_id=change.proposed_room_id,
            starts_at=change.proposed_starts_at,
            ends_at=change.proposed_ends_at,
            timezone=change.proposed_timezone,
            status=schedule.status,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.schedules.add(replacement)
        db.session.flush()
        self.sessions.add(
            ClassSession(
                academy_id=replacement.academy_id,
                branch_id=replacement.branch_id,
                schedule_id=replacement.id,
                status=SESSION_STATUS_FOR_SCHEDULE[ScheduleStatus(replacement.status)],
            )
        )
        db.session.flush()

        schedule.status = ScheduleStatus.RESCHEDULED
        schedule.updated_by = principal.user.id
        schedule.session.status = SESSION_STATUS_FOR_SCHEDULE[
            ScheduleStatus.RESCHEDULED
        ]
        change.status = RescheduleRequestStatus.APPROVED
        change.replacement_schedule_id = replacement.id
        change.decided_by = principal.user.id
        change.decision_reason = decision_reason
        change.decided_at = datetime.now(timezone.utc)

        self._audit(
            principal,
            change,
            "schedule.reschedule_approved",
            previous_data={"status": RescheduleRequestStatus.PENDING},
            new_data=self.serialize(change),
            reason=decision_reason,
        )
        self.audit.record(
            AuditEvent(
                academy_id=schedule.academy_id,
                branch_id=schedule.branch_id,
                actor_user_id=principal.user.id,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action_type="schedule.rescheduled",
                previous_data=previous_schedule,
                new_data=ScheduleService.serialize(schedule),
                reason=change.reason,
            )
        )
        self.audit.record(
            AuditEvent(
                academy_id=replacement.academy_id,
                branch_id=replacement.branch_id,
                actor_user_id=principal.user.id,
                entity_type="schedule",
                entity_id=str(replacement.id),
                action_type="schedule.created_from_reschedule",
                new_data=ScheduleService.serialize(replacement),
                reason=change.reason,
            )
        )
        db.session.commit()
        return change

    def reject(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
        decision_reason: str,
    ) -> ScheduleChangeRequest:
        change = self._request(academy_id, branch_id, request_id, for_update=True)
        schedule = self._schedule(academy_id, branch_id, change.schedule_id)
        self._require_approver(principal, change, schedule)
        self._require_pending(change)
        change.status = RescheduleRequestStatus.REJECTED
        change.decided_by = principal.user.id
        change.decision_reason = decision_reason
        change.decided_at = datetime.now(timezone.utc)
        self._audit(
            principal,
            change,
            "schedule.reschedule_rejected",
            previous_data={"status": RescheduleRequestStatus.PENDING},
            new_data=self.serialize(change),
            reason=decision_reason,
        )
        db.session.commit()
        return change

    @staticmethod
    def serialize(change: ScheduleChangeRequest) -> dict[str, object]:
        return {
            "id": str(change.id),
            "academy_id": str(change.academy_id),
            "branch_id": str(change.branch_id),
            "schedule_id": str(change.schedule_id),
            "replacement_schedule_id": (
                str(change.replacement_schedule_id)
                if change.replacement_schedule_id
                else None
            ),
            "original": {
                "class_id": str(change.original_class_id),
                "teacher_id": str(change.original_teacher_id),
                "room_id": str(change.original_room_id),
                "starts_at": change.original_starts_at.isoformat(),
                "ends_at": change.original_ends_at.isoformat(),
                "timezone": change.original_timezone,
                "status": change.original_status,
            },
            "proposed": {
                "class_id": str(change.original_class_id),
                "teacher_id": str(change.proposed_teacher_id),
                "room_id": str(change.proposed_room_id),
                "starts_at": change.proposed_starts_at.isoformat(),
                "ends_at": change.proposed_ends_at.isoformat(),
                "timezone": change.proposed_timezone,
            },
            "reason": change.reason,
            "status": change.status,
            "requested_by": str(change.requested_by),
            "requester_role": change.requester_role,
            "decided_by": str(change.decided_by) if change.decided_by else None,
            "decision_reason": change.decision_reason,
            "requested_at": change.requested_at.isoformat(),
            "decided_at": change.decided_at.isoformat() if change.decided_at else None,
        }

    def _request(
        self,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
        *,
        for_update: bool = False,
    ) -> ScheduleChangeRequest:
        getter = (
            self.requests.get_scoped_for_update
            if for_update
            else self.requests.get_scoped
        )
        change = getter(academy_id, branch_id, request_id)
        if change is None:
            raise NotFoundError("Reschedule request")
        return change

    def _schedule(
        self, academy_id: UUID, branch_id: UUID, schedule_id: UUID
    ) -> Schedule:
        schedule = self.schedules.get_scoped(academy_id, branch_id, schedule_id)
        if schedule is None:
            raise NotFoundError("Schedule")
        return schedule

    @staticmethod
    def _target(schedule: Schedule) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=schedule.academy_id,
            branch_id=schedule.branch_id,
            class_id=schedule.class_id,
        )

    @staticmethod
    def _candidate(
        schedule: Schedule,
        teacher_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> ScheduleCandidate:
        return ScheduleCandidate(
            academy_id=schedule.academy_id,
            branch_id=schedule.branch_id,
            class_id=schedule.class_id,
            teacher_id=teacher_id,
            room_id=room_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_schedule_id=schedule.id,
        )

    def _requester_role(
        self, principal: Principal, target: AuthorizationTarget
    ) -> Role:
        roles = self._allowed_roles(
            principal, Permission.SCHEDULE_REQUEST_RESCHEDULE, target
        )
        for role in self._requester_role_priority:
            if role in roles:
                return role
        raise AuthorizationError()

    def _require_approver(
        self,
        principal: Principal,
        change: ScheduleChangeRequest,
        schedule: Schedule,
    ) -> None:
        target = self._target(schedule)
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_APPROVE_RESCHEDULE,
            target,
        )
        approver_roles = self._allowed_roles(
            principal, Permission.SCHEDULE_APPROVE_RESCHEDULE, target
        )
        requester_role = Role(change.requester_role)
        if not approver_roles.intersection(self._approvers[requester_role]):
            raise AuthorizationError(
                "This reschedule request requires a higher approval authority.",
                "reschedule_approval_authority_denied",
            )

    @staticmethod
    def _allowed_roles(
        principal: Principal,
        permission: Permission,
        target: AuthorizationTarget,
    ) -> set[Role]:
        roles = set()
        for assignment in principal.assignments:
            if AuthorizationService._assignment_allows(
                assignment,
                permission,
                target,
                principal.user.id,
            ):
                try:
                    roles.add(Role(assignment.role))
                except ValueError:
                    pass
        return roles

    @staticmethod
    def _require_pending(change: ScheduleChangeRequest) -> None:
        if change.status != RescheduleRequestStatus.PENDING:
            raise ConflictError(
                "This reschedule request has already been decided.",
                "reschedule_request_already_decided",
            )

    @staticmethod
    def _require_unchanged_original(
        change: ScheduleChangeRequest, schedule: Schedule
    ) -> None:
        if (
            schedule.class_id != change.original_class_id
            or schedule.teacher_id != change.original_teacher_id
            or schedule.room_id != change.original_room_id
            or schedule.starts_at != change.original_starts_at
            or schedule.ends_at != change.original_ends_at
            or schedule.timezone != change.original_timezone
            or schedule.status != change.original_status
        ):
            raise ConflictError(
                "The original schedule changed after this request was created.",
                "reschedule_original_changed",
            )

    def _audit(
        self,
        principal: Principal,
        change: ScheduleChangeRequest,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
        reason: str,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=change.academy_id,
                branch_id=change.branch_id,
                actor_user_id=principal.user.id,
                entity_type="schedule_change_request",
                entity_id=str(change.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )
