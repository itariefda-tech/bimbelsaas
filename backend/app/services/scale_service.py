from uuid import UUID

from flask import current_app

from app.common.errors import NotFoundError
from app.models.schedule import Schedule
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.branch_repository import BranchRepository
from app.services.authorization_service import AuthorizationService


class ScaleService:
    def __init__(self, branch_repository: BranchRepository | None = None) -> None:
        self.branch_repository = branch_repository or BranchRepository()

    def readiness(self, principal: Principal) -> dict[str, object]:
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        return {
            "cache": {
                "enabled": current_app.config["CACHE_ENABLED"],
                "backend": "redis-ready" if current_app.config.get("REDIS_URL") else "in_memory",
                "redis_configured": bool(current_app.config.get("REDIS_URL")),
                "default_ttl_seconds": current_app.config["CACHE_DEFAULT_TTL_SECONDS"],
            },
            "queues": {
                "notification_worker_concurrency": current_app.config[
                    "QUEUE_WORKER_CONCURRENCY"
                ],
                "realtime_worker_concurrency": current_app.config[
                    "REALTIME_WORKER_CONCURRENCY"
                ],
                "status": "configured",
            },
            "api": {
                "analytics_cache": "enabled",
                "export_cap_rows": current_app.config["EXPORT_MAX_ROWS"],
                "rate_limit_requests": current_app.config["RATE_LIMIT_REQUESTS"],
                "rate_limit_window_seconds": current_app.config[
                    "RATE_LIMIT_WINDOW_SECONDS"
                ],
            },
            "ai_assistant_planning": {
                "status": "planned",
                "guardrails": [
                    "tenant-scoped context only",
                    "no authorization bypass",
                    "human approval for scheduling mutations",
                    "audit every assistant-suggested operation",
                ],
            },
            "deferred_validation": [
                "Redis-backed cache integration test",
                "multi-worker queue throughput test",
                "horizontal app scaling test",
                "AI assistant product validation",
            ],
        }

    def smart_scheduling_signals(
        self,
        principal: Principal,
        branch_id: UUID,
    ) -> dict[str, object]:
        branch = self.branch_repository.get_by_id(branch_id)
        if branch is None:
            raise NotFoundError("Branch")
        AuthorizationService.require(
            principal,
            Permission.SCHEDULE_VIEW,
            AuthorizationTarget(
                academy_id=branch.academy_id,
                branch_id=branch.id,
            ),
        )
        active_student_count = self.branch_repository.active_student_count(
            branch.academy_id,
            branch.id,
        )
        active_teacher_count = self.branch_repository.active_teacher_count(
            branch.academy_id,
            branch.id,
        )
        scheduled_count = Schedule.query.filter_by(
            academy_id=branch.academy_id,
            branch_id=branch.id,
            status="scheduled",
        ).count()
        return {
            "academy_id": str(branch.academy_id),
            "branch_id": str(branch.id),
            "signals": {
                "active_students": active_student_count,
                "active_teachers": active_teacher_count,
                "scheduled_sessions": scheduled_count,
                "student_teacher_ratio": self._ratio(
                    active_student_count,
                    active_teacher_count,
                ),
            },
            "recommendations": self._recommendations(
                active_student_count,
                active_teacher_count,
                scheduled_count,
            ),
            "mutation_policy": "recommendations_only",
        }

    @staticmethod
    def _recommendations(
        active_students: int,
        active_teachers: int,
        scheduled_sessions: int,
    ) -> list[str]:
        recommendations: list[str] = []
        if active_teachers == 0 and active_students > 0:
            recommendations.append("assign_teachers_before_expanding_schedule")
        if active_teachers > 0 and active_students / active_teachers > 20:
            recommendations.append("review_teacher_capacity")
        if scheduled_sessions == 0 and active_students > 0:
            recommendations.append("create_initial_operational_schedule")
        if not recommendations:
            recommendations.append("capacity_signals_normal")
        return recommendations

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)
