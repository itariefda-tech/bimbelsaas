from datetime import date, datetime, time, timezone
from uuid import UUID

from flask import current_app
from sqlalchemy import select

from app.common.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.services.analytics_service import AnalyticsService
from app.services.authorization_service import AuthorizationService


class ExportService:
    def __init__(
        self,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self.academy_repository = academy_repository or AcademyRepository()
        self.branch_repository = branch_repository or BranchRepository()
        self.analytics = analytics or AnalyticsService()

    def audit_logs(
        self,
        principal: Principal,
        *,
        academy_id: UUID | None = None,
        branch_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
    ) -> dict[str, object]:
        target = self._audit_target(academy_id=academy_id, branch_id=branch_id)
        AuthorizationService.require(principal, Permission.AUDIT_LOG_VIEW, target)
        capped_limit = self._capped_limit(limit)
        query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id)
        if academy_id is not None:
            query = query.where(AuditLog.academy_id == academy_id)
        if branch_id is not None:
            query = query.where(AuditLog.branch_id == branch_id)
        if start_date is not None:
            query = query.where(AuditLog.created_at >= self._start_of_day(start_date))
        if end_date is not None:
            query = query.where(AuditLog.created_at <= self._end_of_day(end_date))
        rows = list(db.session.scalars(query.limit(capped_limit + 1)))
        return {
            "export_type": "audit_logs",
            "format": "json",
            "rows": [self._serialize_audit_log(row) for row in rows[:capped_limit]],
            "row_count": min(len(rows), capped_limit),
            "truncated": len(rows) > capped_limit,
            "limit": capped_limit,
        }

    def branch_kpi_report(
        self,
        principal: Principal,
        branch_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        return {
            "export_type": "branch_kpi",
            "format": "json",
            "rows": [
                self.analytics.branch_kpi(
                    principal,
                    branch_id,
                    start_date=start_date,
                    end_date=end_date,
                )
            ],
            "row_count": 1,
            "truncated": False,
            "limit": 1,
        }

    def academy_overview_report(
        self,
        principal: Principal,
        academy_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        return {
            "export_type": "academy_overview",
            "format": "json",
            "rows": [
                self.analytics.academy_overview(
                    principal,
                    academy_id,
                    start_date=start_date,
                    end_date=end_date,
                )
            ],
            "row_count": 1,
            "truncated": False,
            "limit": 1,
        }

    def _audit_target(
        self,
        *,
        academy_id: UUID | None,
        branch_id: UUID | None,
    ) -> AuthorizationTarget:
        if branch_id is not None:
            branch = self.branch_repository.get_by_id(branch_id)
            if branch is None:
                raise NotFoundError("Branch")
            if academy_id is not None and branch.academy_id != academy_id:
                raise ValidationError("branch_id must belong to academy_id.")
            return AuthorizationTarget(
                academy_id=branch.academy_id,
                branch_id=branch.id,
            )
        if academy_id is not None:
            academy = self.academy_repository.get_by_id(academy_id)
            if academy is None:
                raise NotFoundError("Academy")
            return AuthorizationTarget(academy_id=academy.id)
        return AuthorizationTarget()

    @staticmethod
    def _capped_limit(limit: int | None) -> int:
        max_rows = current_app.config["EXPORT_MAX_ROWS"]
        if limit is None:
            return max_rows
        if limit <= 0:
            raise ValidationError("limit must be greater than zero.")
        return min(limit, max_rows)

    @staticmethod
    def _serialize_audit_log(audit_log: AuditLog) -> dict[str, object]:
        return {
            "id": str(audit_log.id),
            "academy_id": str(audit_log.academy_id) if audit_log.academy_id else None,
            "branch_id": str(audit_log.branch_id) if audit_log.branch_id else None,
            "actor_user_id": (
                str(audit_log.actor_user_id) if audit_log.actor_user_id else None
            ),
            "entity_type": audit_log.entity_type,
            "entity_id": audit_log.entity_id,
            "action_type": audit_log.action_type,
            "reason": audit_log.reason,
            "request_id": audit_log.request_id,
            "created_at": audit_log.created_at.isoformat(),
        }

    @staticmethod
    def _start_of_day(value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    @staticmethod
    def _end_of_day(value: date) -> datetime:
        return datetime.combine(value, time.max, tzinfo=timezone.utc)
