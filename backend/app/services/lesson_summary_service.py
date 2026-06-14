from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import AuthorizationError, ConflictError, NotFoundError
from app.domain.lesson_summary_status import (
    LessonSummaryEditRequestStatus,
    LessonSummaryStatus,
)
from app.extensions import db
from app.models.class_session import ClassSession
from app.models.lesson_summary import LessonSummary
from app.models.lesson_summary_edit_request import LessonSummaryEditRequest
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.lesson_summary_repository import (
    LessonSummaryEditRequestRepository,
    LessonSummaryRepository,
)
from app.repositories.schedule_repository import ClassSessionRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.parent_notification_service import ParentNotificationService


class LessonSummaryService:
    _content_fields = (
        "lesson_topic",
        "class_summary",
        "teacher_notes",
        "homework",
        "student_attention_notes",
    )

    def __init__(
        self,
        sessions: ClassSessionRepository | None = None,
        summaries: LessonSummaryRepository | None = None,
        requests: LessonSummaryEditRequestRepository | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.sessions = sessions or ClassSessionRepository()
        self.summaries = summaries or LessonSummaryRepository()
        self.requests = requests or LessonSummaryEditRequestRepository()
        self.audit = audit or AuditLogService()

    def get_for_session(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> LessonSummary | None:
        session = self._session(academy_id, branch_id, session_id)
        AuthorizationService.require(
            principal,
            Permission.LESSON_SUMMARY_VIEW,
            self._target(session),
        )
        return self.summaries.get_for_session(session_id)

    def save_draft(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
        content: dict[str, str | None],
    ) -> LessonSummary:
        session = self._session(academy_id, branch_id, session_id, for_update=True)
        target = self._target(session)
        summary = self.summaries.get_for_session(session_id)
        if summary is None:
            AuthorizationService.require(
                principal,
                Permission.LESSON_SUMMARY_CREATE,
                target,
            )
            if session.schedule.teacher.user_id != principal.user.id:
                raise AuthorizationError(
                    "Only the assigned teacher can create this lesson summary.",
                    "lesson_summary_teacher_mismatch",
                )
            summary = LessonSummary(
                academy_id=academy_id,
                branch_id=branch_id,
                session_id=session.id,
                schedule_id=session.schedule_id,
                class_id=session.schedule.class_id,
                teacher_id=session.schedule.teacher_id,
                created_by=principal.user.id,
                updated_by=principal.user.id,
                **content,
            )
            self.summaries.add(summary)
            action = "lesson_summary.created"
            previous = None
        else:
            AuthorizationService.require(
                principal,
                Permission.LESSON_SUMMARY_EDIT,
                target,
            )
            if summary.status == LessonSummaryStatus.PUBLISHED:
                raise ConflictError(
                    "Published lesson summaries require an approved edit request.",
                    "lesson_summary_published",
                )
            previous = self.serialize(summary)
            self._apply_content(summary, content)
            summary.updated_by = principal.user.id
            action = "lesson_summary.draft_updated"
        db.session.flush()
        self._audit(
            principal,
            summary,
            action,
            previous_data=previous,
            new_data=self.serialize(summary),
        )
        ParentNotificationService().emit_for_class(
            academy_id=academy_id,
            branch_id=branch_id,
            class_id=summary.class_id,
            notification_type="lesson_summary.published",
            priority="medium",
            title="New lesson summary",
            payload={
                "session_id": str(session.id),
                "lesson_summary_id": str(summary.id),
            },
            dedup_key=f"lesson_summary.published:{summary.id}",
        )
        db.session.commit()
        return summary

    def publish(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> LessonSummary:
        session = self._session(academy_id, branch_id, session_id, for_update=True)
        AuthorizationService.require(
            principal,
            Permission.LESSON_SUMMARY_PUBLISH,
            self._target(session),
        )
        summary = self.summaries.get_for_session(session_id)
        if summary is None:
            raise NotFoundError("Lesson summary")
        if summary.status == LessonSummaryStatus.PUBLISHED:
            raise ConflictError(
                "Lesson summary is already published.",
                "lesson_summary_already_published",
            )
        previous = self.serialize(summary)
        summary.status = LessonSummaryStatus.PUBLISHED
        summary.published_by = principal.user.id
        summary.published_at = datetime.now(timezone.utc)
        summary.updated_by = principal.user.id
        self._audit(
            principal,
            summary,
            "lesson_summary.published",
            previous_data=previous,
            new_data=self.serialize(summary),
        )
        db.session.commit()
        return summary

    def request_edit(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        summary_id: UUID,
        content: dict[str, str | None],
        reason: str,
    ) -> LessonSummaryEditRequest:
        summary = self._summary(academy_id, branch_id, summary_id)
        AuthorizationService.require(
            principal,
            Permission.LESSON_SUMMARY_REQUEST_EDIT,
            self._summary_target(summary),
        )
        if summary.status != LessonSummaryStatus.PUBLISHED:
            raise ConflictError(
                "Draft lesson summaries can be edited directly.",
                "lesson_summary_not_published",
            )
        if self.requests.pending_for_summary(summary.id):
            raise ConflictError(
                "A pending lesson summary edit request already exists.",
                "pending_lesson_summary_edit_exists",
            )
        original = self.content(summary)
        if original == content:
            raise ConflictError(
                "The proposed lesson summary is unchanged.",
                "lesson_summary_edit_has_no_changes",
            )
        request = LessonSummaryEditRequest(
            academy_id=academy_id,
            branch_id=branch_id,
            lesson_summary_id=summary.id,
            original_data=original,
            proposed_data=content,
            reason=reason,
            requested_by=principal.user.id,
        )
        self.requests.add(request)
        db.session.flush()
        self._audit_request(
            principal,
            request,
            "lesson_summary.edit_requested",
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
    ) -> LessonSummaryEditRequest:
        request = self.requests.get_scoped_for_update(
            academy_id,
            branch_id,
            request_id,
        )
        if request is None:
            raise NotFoundError("Lesson summary edit request")
        summary = request.lesson_summary
        AuthorizationService.require(
            principal,
            Permission.LESSON_SUMMARY_APPROVE_EDIT,
            self._summary_target(summary),
        )
        if request.requested_by == principal.user.id:
            raise AuthorizationError(
                "Lesson summary edit requests cannot be self-approved.",
                "lesson_summary_edit_self_approval_denied",
            )
        if request.status != LessonSummaryEditRequestStatus.PENDING:
            raise ConflictError(
                "This lesson summary edit request has already been decided.",
                "lesson_summary_edit_already_decided",
            )
        if self.content(summary) != request.original_data:
            raise ConflictError(
                "Lesson summary changed after this request was created.",
                "lesson_summary_edit_original_changed",
            )
        previous = self.serialize(summary)
        request.status = (
            LessonSummaryEditRequestStatus.APPROVED
            if approve
            else LessonSummaryEditRequestStatus.REJECTED
        )
        request.decided_by = principal.user.id
        request.decision_reason = reason
        request.decided_at = datetime.now(timezone.utc)
        if approve:
            self._apply_content(summary, request.proposed_data)
            summary.updated_by = principal.user.id
            self._audit(
                principal,
                summary,
                "lesson_summary.published_edit_applied",
                previous_data=previous,
                new_data=self.serialize(summary),
                reason=request.reason,
            )
        self._audit_request(
            principal,
            request,
            (
                "lesson_summary.edit_approved"
                if approve
                else "lesson_summary.edit_rejected"
            ),
            previous_data={"status": LessonSummaryEditRequestStatus.PENDING},
            new_data=self.serialize_request(request),
            reason=reason,
        )
        db.session.commit()
        return request

    @staticmethod
    def content(summary: LessonSummary) -> dict[str, str | None]:
        return {
            field: getattr(summary, field)
            for field in LessonSummaryService._content_fields
        }

    @staticmethod
    def serialize(summary: LessonSummary) -> dict[str, object]:
        return {
            "id": str(summary.id),
            "session_id": str(summary.session_id),
            "schedule_id": str(summary.schedule_id),
            "class_id": str(summary.class_id),
            "teacher_id": str(summary.teacher_id),
            **LessonSummaryService.content(summary),
            "status": summary.status,
            "created_by": str(summary.created_by),
            "updated_by": str(summary.updated_by),
            "published_by": (
                str(summary.published_by) if summary.published_by else None
            ),
            "published_at": (
                summary.published_at.isoformat() if summary.published_at else None
            ),
        }

    @staticmethod
    def serialize_request(request: LessonSummaryEditRequest) -> dict[str, object]:
        return {
            "id": str(request.id),
            "lesson_summary_id": str(request.lesson_summary_id),
            "original": request.original_data,
            "proposed": request.proposed_data,
            "reason": request.reason,
            "status": request.status,
            "requested_by": str(request.requested_by),
            "decided_by": str(request.decided_by) if request.decided_by else None,
            "decision_reason": request.decision_reason,
        }

    @staticmethod
    def _apply_content(
        summary: LessonSummary,
        content: dict[str, str | None],
    ) -> None:
        for field in LessonSummaryService._content_fields:
            setattr(summary, field, content[field])

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

    def _summary(
        self,
        academy_id: UUID,
        branch_id: UUID,
        summary_id: UUID,
    ) -> LessonSummary:
        summary = self.summaries.get_scoped(academy_id, branch_id, summary_id)
        if summary is None:
            raise NotFoundError("Lesson summary")
        return summary

    @staticmethod
    def _target(session: ClassSession) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=session.academy_id,
            branch_id=session.branch_id,
            class_id=session.schedule.class_id,
        )

    @staticmethod
    def _summary_target(summary: LessonSummary) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=summary.academy_id,
            branch_id=summary.branch_id,
            class_id=summary.class_id,
        )

    def _audit(
        self,
        principal: Principal,
        summary: LessonSummary,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
        reason: str | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=summary.academy_id,
                branch_id=summary.branch_id,
                actor_user_id=principal.user.id,
                entity_type="lesson_summary",
                entity_id=str(summary.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )

    def _audit_request(
        self,
        principal: Principal,
        request: LessonSummaryEditRequest,
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
                entity_type="lesson_summary_edit_request",
                entity_id=str(request.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
                reason=reason,
            )
        )
