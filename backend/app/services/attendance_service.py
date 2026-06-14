from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.domain.attendance_status import (
    AttendanceEditRequestStatus,
    AttendanceSheetStatus,
    AttendanceStatus,
)
from app.extensions import db
from app.models.attendance import Attendance
from app.models.attendance_edit_request import AttendanceEditRequest
from app.models.class_session import ClassSession
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.attendance_repository import (
    AttendanceEditRequestRepository,
    AttendanceRepository,
)
from app.repositories.class_repository import ClassStudentRepository
from app.repositories.schedule_repository import ClassSessionRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.parent_notification_service import ParentNotificationService


class AttendanceService:
    def __init__(
        self,
        sessions: ClassSessionRepository | None = None,
        attendances: AttendanceRepository | None = None,
        requests: AttendanceEditRequestRepository | None = None,
        enrollments: ClassStudentRepository | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.sessions = sessions or ClassSessionRepository()
        self.attendances = attendances or AttendanceRepository()
        self.requests = requests or AttendanceEditRequestRepository()
        self.enrollments = enrollments or ClassStudentRepository()
        self.audit = audit or AuditLogService()

    def get_sheet(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> dict[str, object]:
        session = self._session(academy_id, branch_id, session_id)
        AuthorizationService.require(
            principal,
            Permission.ATTENDANCE_VIEW,
            self._target(session),
        )
        return self.serialize_sheet(
            session,
            self.attendances.list_for_session(
                academy_id,
                branch_id,
                session_id,
            ),
        )

    def save_draft(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
        entries: list[dict[str, object]],
    ) -> dict[str, object]:
        session = self._session(academy_id, branch_id, session_id, for_update=True)
        target = self._target(session)
        if session.attendance_status == AttendanceSheetStatus.FINALIZED:
            raise ConflictError(
                "Finalized attendance requires an approved edit request.",
                "attendance_finalized",
            )
        enrolled_ids = self._enrolled_student_ids(session)
        seen: set[UUID] = set()
        for entry in entries:
            student_id = entry["student_id"]
            if student_id in seen:
                raise ConflictError(
                    "A student may only appear once in an attendance update.",
                    "duplicate_attendance_student",
                )
            seen.add(student_id)
            if student_id not in enrolled_ids:
                raise ConflictError(
                    "Attendance can only be recorded for active class students.",
                    "student_not_enrolled",
                )
            existing = self.attendances.get_for_session_student(
                session.id,
                student_id,
            )
            permission = (
                Permission.ATTENDANCE_EDIT
                if existing
                else Permission.ATTENDANCE_CREATE
            )
            AuthorizationService.require(principal, permission, target)
            status = self._status(entry["attendance_status"])
            note = entry.get("note")
            previous = self.serialize(existing) if existing else None
            if existing is None:
                existing = Attendance(
                    academy_id=academy_id,
                    branch_id=branch_id,
                    session_id=session.id,
                    schedule_id=session.schedule_id,
                    class_id=session.schedule.class_id,
                    student_id=student_id,
                    attendance_status=status,
                    note=note,
                    recorded_by=principal.user.id,
                    updated_by=principal.user.id,
                )
                self.attendances.add(existing)
                action = "attendance.recorded"
            else:
                existing.attendance_status = status
                existing.note = note
                existing.updated_by = principal.user.id
                action = "attendance.updated"
            db.session.flush()
            self._audit(
                principal,
                existing,
                action,
                previous_data=previous,
                new_data=self.serialize(existing),
            )
        db.session.commit()
        return self.get_sheet(
            principal,
            academy_id=academy_id,
            branch_id=branch_id,
            session_id=session_id,
        )

    def finalize(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> dict[str, object]:
        session = self._session(academy_id, branch_id, session_id, for_update=True)
        AuthorizationService.require(
            principal,
            Permission.ATTENDANCE_FINALIZE,
            self._target(session),
        )
        if session.attendance_status == AttendanceSheetStatus.FINALIZED:
            raise ConflictError(
                "Attendance is already finalized.",
                "attendance_already_finalized",
            )
        enrolled_ids = self._enrolled_student_ids(session)
        recorded = self.attendances.list_for_session(
            academy_id,
            branch_id,
            session_id,
        )
        if not enrolled_ids or {item.student_id for item in recorded} != enrolled_ids:
            raise ConflictError(
                "Every active class student must have attendance before finalization.",
                "attendance_incomplete",
            )
        session.attendance_status = AttendanceSheetStatus.FINALIZED
        session.attendance_finalized_by = principal.user.id
        session.attendance_finalized_at = datetime.now(timezone.utc)
        self.audit.record(
            AuditEvent(
                academy_id=academy_id,
                branch_id=branch_id,
                actor_user_id=principal.user.id,
                entity_type="class_session",
                entity_id=str(session.id),
                action_type="attendance.finalized",
                previous_data={"attendance_status": AttendanceSheetStatus.DRAFT},
                new_data={
                    "attendance_status": AttendanceSheetStatus.FINALIZED,
                    "attendance_count": len(recorded),
                },
            )
        )
        ParentNotificationService().emit_for_class(
            academy_id=academy_id,
            branch_id=branch_id,
            class_id=session.schedule.class_id,
            notification_type="attendance.finalized",
            priority="medium",
            title="Attendance is available",
            payload={"session_id": str(session.id)},
            dedup_key=f"attendance.finalized:{session.id}",
        )
        db.session.commit()
        return self.serialize_sheet(session, recorded)

    def request_edit(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        attendance_id: UUID,
        proposed_status: str,
        proposed_note: str | None,
        reason: str,
    ) -> AttendanceEditRequest:
        attendance = self._attendance(academy_id, branch_id, attendance_id)
        AuthorizationService.require(
            principal,
            Permission.ATTENDANCE_REQUEST_EDIT,
            self._attendance_target(attendance),
        )
        if attendance.session.attendance_status != AttendanceSheetStatus.FINALIZED:
            raise ConflictError(
                "Draft attendance can be edited directly.",
                "attendance_not_finalized",
            )
        if self.requests.pending_for_attendance(attendance.id):
            raise ConflictError(
                "A pending edit request already exists for this attendance.",
                "pending_attendance_edit_exists",
            )
        status = self._status(proposed_status)
        if status == attendance.attendance_status and proposed_note == attendance.note:
            raise ConflictError(
                "The proposed attendance is unchanged.",
                "attendance_edit_has_no_changes",
            )
        request = AttendanceEditRequest(
            academy_id=academy_id,
            branch_id=branch_id,
            attendance_id=attendance.id,
            original_status=attendance.attendance_status,
            original_note=attendance.note,
            proposed_status=status,
            proposed_note=proposed_note,
            reason=reason,
            requested_by=principal.user.id,
        )
        self.requests.add(request)
        db.session.flush()
        self._audit_request(
            principal,
            request,
            "attendance.edit_requested",
            new_data=self.serialize_request(request),
            reason=reason,
        )
        db.session.commit()
        return request

    def decide_edit(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
        approve: bool,
        reason: str,
    ) -> AttendanceEditRequest:
        request = self.requests.get_scoped_for_update(
            academy_id,
            branch_id,
            request_id,
        )
        if request is None:
            raise NotFoundError("Attendance edit request")
        attendance = request.attendance
        AuthorizationService.require(
            principal,
            Permission.ATTENDANCE_APPROVE_EDIT,
            self._attendance_target(attendance),
        )
        if request.requested_by == principal.user.id:
            raise AuthorizationError(
                "Attendance edit requests cannot be self-approved.",
                "attendance_edit_self_approval_denied",
            )
        if request.status != AttendanceEditRequestStatus.PENDING:
            raise ConflictError(
                "This attendance edit request has already been decided.",
                "attendance_edit_already_decided",
            )
        if (
            attendance.attendance_status != request.original_status
            or attendance.note != request.original_note
        ):
            raise ConflictError(
                "Attendance changed after this edit request was created.",
                "attendance_edit_original_changed",
            )
        previous = self.serialize(attendance)
        request.status = (
            AttendanceEditRequestStatus.APPROVED
            if approve
            else AttendanceEditRequestStatus.REJECTED
        )
        request.decided_by = principal.user.id
        request.decision_reason = reason
        request.decided_at = datetime.now(timezone.utc)
        if approve:
            attendance.attendance_status = request.proposed_status
            attendance.note = request.proposed_note
            attendance.updated_by = principal.user.id
            self._audit(
                principal,
                attendance,
                "attendance.finalized_edit_applied",
                previous_data=previous,
                new_data=self.serialize(attendance),
                reason=request.reason,
            )
        self._audit_request(
            principal,
            request,
            (
                "attendance.edit_approved"
                if approve
                else "attendance.edit_rejected"
            ),
            previous_data={"status": AttendanceEditRequestStatus.PENDING},
            new_data=self.serialize_request(request),
            reason=reason,
        )
        db.session.commit()
        return request

    @staticmethod
    def serialize(attendance: Attendance) -> dict[str, object]:
        return {
            "id": str(attendance.id),
            "session_id": str(attendance.session_id),
            "schedule_id": str(attendance.schedule_id),
            "class_id": str(attendance.class_id),
            "student_id": str(attendance.student_id),
            "attendance_status": attendance.attendance_status,
            "note": attendance.note,
            "recorded_by": str(attendance.recorded_by),
            "updated_by": str(attendance.updated_by),
            "recorded_at": attendance.recorded_at.isoformat(),
            "updated_at": attendance.updated_at.isoformat(),
        }

    @staticmethod
    def serialize_sheet(
        session: ClassSession,
        attendances: list[Attendance],
    ) -> dict[str, object]:
        return {
            "session_id": str(session.id),
            "schedule_id": str(session.schedule_id),
            "attendance_status": session.attendance_status,
            "finalized_by": (
                str(session.attendance_finalized_by)
                if session.attendance_finalized_by
                else None
            ),
            "finalized_at": (
                session.attendance_finalized_at.isoformat()
                if session.attendance_finalized_at
                else None
            ),
            "entries": [AttendanceService.serialize(item) for item in attendances],
        }

    @staticmethod
    def serialize_request(request: AttendanceEditRequest) -> dict[str, object]:
        return {
            "id": str(request.id),
            "attendance_id": str(request.attendance_id),
            "original": {
                "attendance_status": request.original_status,
                "note": request.original_note,
            },
            "proposed": {
                "attendance_status": request.proposed_status,
                "note": request.proposed_note,
            },
            "reason": request.reason,
            "status": request.status,
            "requested_by": str(request.requested_by),
            "decided_by": str(request.decided_by) if request.decided_by else None,
            "decision_reason": request.decision_reason,
        }

    def _session(
        self,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> ClassSession:
        getter = (
            self.sessions.get_scoped_for_update
            if for_update
            else self.sessions.get_scoped
        )
        session = getter(academy_id, branch_id, session_id)
        if session is None:
            raise NotFoundError("Class session")
        return session

    def _attendance(
        self,
        academy_id: UUID,
        branch_id: UUID,
        attendance_id: UUID,
    ) -> Attendance:
        attendance = self.attendances.get_scoped(
            academy_id,
            branch_id,
            attendance_id,
        )
        if attendance is None:
            raise NotFoundError("Attendance")
        return attendance

    def _enrolled_student_ids(self, session: ClassSession) -> set[UUID]:
        return {
            item.student_id
            for item in self.enrollments.list_active_for_class(
                session.schedule.class_id
            )
        }

    @staticmethod
    def _target(session: ClassSession) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=session.academy_id,
            branch_id=session.branch_id,
            class_id=session.schedule.class_id,
        )

    @staticmethod
    def _attendance_target(attendance: Attendance) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=attendance.academy_id,
            branch_id=attendance.branch_id,
            class_id=attendance.class_id,
            student_id=attendance.student_id,
        )

    @staticmethod
    def _status(value: object) -> AttendanceStatus:
        try:
            return AttendanceStatus(str(value))
        except ValueError as error:
            raise ValidationError(
                "Invalid attendance status.",
                details={"attendance_status": "invalid"},
            ) from error

    def _audit(
        self,
        principal: Principal,
        attendance: Attendance,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
        reason: str | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=attendance.academy_id,
                branch_id=attendance.branch_id,
                actor_user_id=principal.user.id,
                entity_type="attendance",
                entity_id=str(attendance.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )

    def _audit_request(
        self,
        principal: Principal,
        request: AttendanceEditRequest,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
        reason: str,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=request.academy_id,
                branch_id=request.branch_id,
                actor_user_id=principal.user.id,
                entity_type="attendance_edit_request",
                entity_id=str(request.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )
