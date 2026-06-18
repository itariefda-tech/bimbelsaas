from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.beta_status import (
    BETA_FEEDBACK_TRANSITIONS,
    BETA_ONBOARDING_TRANSITIONS,
    BetaFeedbackSeverity,
    BetaFeedbackStatus,
    BetaOnboardingStatus,
)
from app.extensions import db
from app.models.beta import BetaAcademyOnboarding, BetaFeedback
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService

FEEDBACK_CATEGORIES = frozenset(
    {
        "bug",
        "workflow",
        "parent_ux",
        "teacher_ux",
        "performance",
        "data_quality",
        "other",
    }
)


class BetaService:
    def __init__(
        self,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.academy_repository = academy_repository or AcademyRepository()
        self.branch_repository = branch_repository or BranchRepository()
        self.audit = audit or AuditLogService()

    def create_onboarding(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        cohort_label: str,
        operational_owner_name: str,
        operational_owner_contact: str,
        success_criteria: dict,
        target_start_date,
        target_end_date,
        notes: str | None,
    ) -> BetaAcademyOnboarding:
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        if self.academy_repository.get_by_id(academy_id) is None:
            raise NotFoundError("Academy")
        onboarding = BetaAcademyOnboarding(
            academy_id=academy_id,
            cohort_label=self._required_text(cohort_label, "cohort_label"),
            operational_owner_name=self._required_text(
                operational_owner_name,
                "operational_owner_name",
            ),
            operational_owner_contact=self._required_text(
                operational_owner_contact,
                "operational_owner_contact",
            ),
            success_criteria=self._criteria(success_criteria),
            target_start_date=target_start_date,
            target_end_date=target_end_date,
            notes=self._optional_text(notes),
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self._validate_dates(onboarding.target_start_date, onboarding.target_end_date)
        db.session.add(onboarding)
        db.session.flush()
        self._audit_onboarding(principal, onboarding, "beta.onboarding_created")
        db.session.commit()
        return onboarding

    def update_onboarding_status(
        self,
        principal: Principal,
        onboarding_id: UUID,
        *,
        status: str,
        notes: str | None = None,
    ) -> BetaAcademyOnboarding:
        onboarding = self._get_onboarding(onboarding_id)
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        previous = self.serialize_onboarding(onboarding)
        current_status = BetaOnboardingStatus(onboarding.status)
        next_status = self._enum_value(BetaOnboardingStatus, status, "status")
        if next_status not in BETA_ONBOARDING_TRANSITIONS[current_status]:
            raise ConflictError("Invalid beta onboarding status transition.")
        onboarding.status = next_status.value
        onboarding.notes = self._optional_text(notes) or onboarding.notes
        onboarding.updated_by = principal.user.id
        self._audit_onboarding(
            principal,
            onboarding,
            "beta.onboarding_status_changed",
            previous_data=previous,
        )
        db.session.commit()
        return onboarding

    def list_onboardings(self, principal: Principal) -> list[BetaAcademyOnboarding]:
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        return list(
            db.session.scalars(
                select(BetaAcademyOnboarding).order_by(
                    BetaAcademyOnboarding.created_at.desc()
                )
            )
        )

    def submit_feedback(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID | None,
        category: str,
        severity: str,
        source_role: str,
        summary: str,
        details: str | None,
    ) -> BetaFeedback:
        target = self._feedback_target(academy_id, branch_id)
        AuthorizationService.require(principal, Permission.ACADEMY_VIEW, target)
        normalized_category = self._category(category)
        normalized_severity = self._enum_value(
            BetaFeedbackSeverity,
            severity,
            "severity",
        )
        feedback = BetaFeedback(
            academy_id=academy_id,
            branch_id=branch_id,
            reporter_user_id=principal.user.id,
            category=normalized_category,
            severity=normalized_severity.value,
            source_role=self._required_text(source_role, "source_role"),
            summary=self._required_text(summary, "summary", max_length=200),
            details=self._optional_text(details),
        )
        db.session.add(feedback)
        db.session.flush()
        self._audit_feedback(principal, feedback, "beta.feedback_submitted")
        db.session.commit()
        return feedback

    def list_feedback(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID | None = None,
        status: str | None = None,
    ) -> list[BetaFeedback]:
        target = self._feedback_target(academy_id, branch_id)
        AuthorizationService.require(principal, Permission.REPORT_VIEW, target)
        query = select(BetaFeedback).where(BetaFeedback.academy_id == academy_id)
        if branch_id is not None:
            query = query.where(BetaFeedback.branch_id == branch_id)
        if status not in (None, ""):
            query = query.where(
                BetaFeedback.status
                == self._enum_value(BetaFeedbackStatus, status, "status").value
            )
        return list(
            db.session.scalars(query.order_by(BetaFeedback.created_at.desc()))
        )

    def update_feedback_status(
        self,
        principal: Principal,
        feedback_id: UUID,
        *,
        status: str,
        resolution_notes: str | None = None,
    ) -> BetaFeedback:
        feedback = self._get_feedback(feedback_id)
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(
                academy_id=feedback.academy_id,
                branch_id=feedback.branch_id,
            ),
        )
        previous = self.serialize_feedback(feedback)
        current_status = BetaFeedbackStatus(feedback.status)
        next_status = self._enum_value(BetaFeedbackStatus, status, "status")
        if next_status not in BETA_FEEDBACK_TRANSITIONS[current_status]:
            raise ConflictError("Invalid beta feedback status transition.")
        feedback.status = next_status.value
        feedback.resolution_notes = (
            self._optional_text(resolution_notes) or feedback.resolution_notes
        )
        if next_status in {BetaFeedbackStatus.RESOLVED, BetaFeedbackStatus.CLOSED}:
            feedback.resolved_at = datetime.now(timezone.utc)
        self._audit_feedback(
            principal,
            feedback,
            "beta.feedback_status_changed",
            previous_data=previous,
        )
        db.session.commit()
        return feedback

    def readiness(self, principal: Principal) -> dict[str, object]:
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        active_onboardings = db.session.scalar(
            select(func.count(BetaAcademyOnboarding.id)).where(
                BetaAcademyOnboarding.status == BetaOnboardingStatus.ACTIVE
            )
        ) or 0
        open_feedback = db.session.scalar(
            select(func.count(BetaFeedback.id)).where(
                BetaFeedback.status.in_(
                    [
                        BetaFeedbackStatus.OPEN,
                        BetaFeedbackStatus.TRIAGED,
                        BetaFeedbackStatus.IN_PROGRESS,
                    ]
                )
            )
        ) or 0
        critical_feedback = db.session.scalar(
            select(func.count(BetaFeedback.id)).where(
                BetaFeedback.severity == BetaFeedbackSeverity.CRITICAL,
                BetaFeedback.status != BetaFeedbackStatus.CLOSED,
            )
        ) or 0
        return {
            "phase": "beta_launch_preparation",
            "ready_for_limited_beta": active_onboardings > 0 and critical_feedback == 0,
            "active_onboardings": active_onboardings,
            "open_feedback": open_feedback,
            "critical_feedback": critical_feedback,
            "checklist": {
                "beta_academy_onboarding": active_onboardings > 0,
                "real_operational_testing": active_onboardings > 0,
                "parent_ux_observation": True,
                "teacher_ux_observation": True,
                "bug_feedback_intake": True,
                "performance_monitoring": True,
            },
            "staging_dependencies": {
                "load_testing": "requires deployed staging traffic harness",
                "backup_recovery": "requires PostgreSQL runtime and storage target",
                "websocket_soak": "requires multi-client realtime staging run",
            },
        }

    @staticmethod
    def serialize_onboarding(onboarding: BetaAcademyOnboarding) -> dict[str, object]:
        return {
            "id": str(onboarding.id),
            "academy_id": str(onboarding.academy_id),
            "cohort_label": onboarding.cohort_label,
            "status": onboarding.status,
            "operational_owner_name": onboarding.operational_owner_name,
            "operational_owner_contact": onboarding.operational_owner_contact,
            "success_criteria": onboarding.success_criteria,
            "target_start_date": (
                onboarding.target_start_date.isoformat()
                if onboarding.target_start_date
                else None
            ),
            "target_end_date": (
                onboarding.target_end_date.isoformat()
                if onboarding.target_end_date
                else None
            ),
            "notes": onboarding.notes,
            "created_at": onboarding.created_at.isoformat(),
            "updated_at": onboarding.updated_at.isoformat(),
        }

    @staticmethod
    def serialize_feedback(feedback: BetaFeedback) -> dict[str, object]:
        return {
            "id": str(feedback.id),
            "academy_id": str(feedback.academy_id),
            "branch_id": str(feedback.branch_id) if feedback.branch_id else None,
            "reporter_user_id": (
                str(feedback.reporter_user_id) if feedback.reporter_user_id else None
            ),
            "category": feedback.category,
            "severity": feedback.severity,
            "status": feedback.status,
            "source_role": feedback.source_role,
            "summary": feedback.summary,
            "details": feedback.details,
            "resolution_notes": feedback.resolution_notes,
            "created_at": feedback.created_at.isoformat(),
            "updated_at": feedback.updated_at.isoformat(),
            "resolved_at": feedback.resolved_at.isoformat()
            if feedback.resolved_at
            else None,
        }

    def _get_onboarding(self, onboarding_id: UUID) -> BetaAcademyOnboarding:
        onboarding = db.session.get(BetaAcademyOnboarding, onboarding_id)
        if onboarding is None:
            raise NotFoundError("Beta onboarding")
        return onboarding

    def _get_feedback(self, feedback_id: UUID) -> BetaFeedback:
        feedback = db.session.get(BetaFeedback, feedback_id)
        if feedback is None:
            raise NotFoundError("Beta feedback")
        return feedback

    def _feedback_target(
        self,
        academy_id: UUID,
        branch_id: UUID | None,
    ) -> AuthorizationTarget:
        if self.academy_repository.get_by_id(academy_id) is None:
            raise NotFoundError("Academy")
        if branch_id is not None:
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise NotFoundError("Branch")
            if branch.academy_id != academy_id:
                raise ValidationError("branch_id must belong to academy_id.")
        return AuthorizationTarget(academy_id=academy_id, branch_id=branch_id)

    @staticmethod
    def _required_text(value: str, field: str, *, max_length: int = 500) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field} is required.")
        normalized = value.strip()
        if len(normalized) > max_length:
            raise ValidationError(f"{field} must be {max_length} characters or less.")
        return normalized

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise ValidationError("Text fields must be strings.")
        return value.strip()

    @staticmethod
    def _criteria(value: dict) -> dict:
        if not isinstance(value, dict):
            raise ValidationError("success_criteria must be an object.")
        return value

    @staticmethod
    def _validate_dates(start_date, end_date) -> None:
        if start_date and end_date and end_date < start_date:
            raise ValidationError("target_end_date must be on or after target_start_date.")

    @staticmethod
    def _enum_value(enum_type, value: str, field: str):
        try:
            return enum_type(value)
        except ValueError as error:
            raise ValidationError(f"{field} is invalid.") from error

    @staticmethod
    def _category(value: str) -> str:
        if value not in FEEDBACK_CATEGORIES:
            raise ValidationError("category is invalid.")
        return value

    def _audit_onboarding(
        self,
        principal: Principal,
        onboarding: BetaAcademyOnboarding,
        action: str,
        previous_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=onboarding.academy_id,
                actor_user_id=principal.user.id,
                entity_type="beta_onboarding",
                entity_id=str(onboarding.id),
                action_type=action,
                previous_data=previous_data,
                new_data=self.serialize_onboarding(onboarding),
            )
        )

    def _audit_feedback(
        self,
        principal: Principal,
        feedback: BetaFeedback,
        action: str,
        previous_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=feedback.academy_id,
                branch_id=feedback.branch_id,
                actor_user_id=principal.user.id,
                entity_type="beta_feedback",
                entity_id=str(feedback.id),
                action_type=action,
                previous_data=previous_data,
                new_data=self.serialize_feedback(feedback),
            )
        )
