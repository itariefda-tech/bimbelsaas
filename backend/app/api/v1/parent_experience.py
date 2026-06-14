from datetime import datetime, timedelta, timezone
from uuid import UUID

from flask import Blueprint, g, request

from app.common.errors import ValidationError
from app.common.responses import success_response
from app.permissions.decorators import require_auth
from app.services.parent_experience_service import ParentExperienceService

parent_experience_api = Blueprint("parent_experience", __name__)


@parent_experience_api.get("/parent/dashboard")
@require_auth
def parent_dashboard():
    data = ParentExperienceService().dashboard(g.principal, _academy_id())
    return success_response(data=data, message="Parent dashboard loaded.")


@parent_experience_api.get("/parent/children")
@require_auth
def linked_children():
    data = ParentExperienceService().list_children(g.principal, _academy_id())
    return success_response(data=data, message="Linked children loaded.")


@parent_experience_api.get("/parent/children/<uuid:student_id>/overview")
@require_auth
def child_overview(student_id):
    data = ParentExperienceService().overview(
        g.principal,
        _academy_id(),
        student_id,
    )
    return success_response(data=data, message="Child overview loaded.")


@parent_experience_api.get("/parent/children/<uuid:student_id>/attendance")
@require_auth
def child_attendance(student_id):
    limit = _limit()
    data = ParentExperienceService().attendance_history(
        g.principal,
        _academy_id(),
        student_id,
        limit,
    )
    return success_response(
        data=data,
        message="Attendance history loaded.",
        meta={"limit": limit, "count": len(data)},
    )


@parent_experience_api.get("/parent/children/<uuid:student_id>/progress")
@require_auth
def child_progress(student_id):
    data = ParentExperienceService().academic_progress(
        g.principal,
        _academy_id(),
        student_id,
    )
    return success_response(data=data, message="Academic progress loaded.")


@parent_experience_api.get(
    "/parent/children/<uuid:student_id>/lesson-summaries"
)
@require_auth
def child_lesson_summaries(student_id):
    limit = _limit()
    data = ParentExperienceService().published_summaries(
        g.principal,
        _academy_id(),
        student_id,
        limit,
    )
    return success_response(
        data=data,
        message="Published lesson summaries loaded.",
        meta={"limit": limit, "count": len(data)},
    )


@parent_experience_api.get("/parent/children/<uuid:student_id>/schedule")
@require_auth
def child_schedule(student_id):
    now = datetime.now(timezone.utc)
    starts_at = _datetime_arg("from", now - timedelta(days=7))
    ends_at = _datetime_arg("to", now + timedelta(days=30))
    data = ParentExperienceService().schedule_overview(
        g.principal,
        _academy_id(),
        student_id,
        starts_at,
        ends_at,
        request.args.get("timezone", "Asia/Jakarta").strip(),
    )
    return success_response(data=data, message="Schedule overview loaded.")


def _academy_id() -> UUID:
    academy_id = g.principal.user.academy_id
    if academy_id is None:
        raise ValidationError("A parent academy is required.")
    return academy_id


def _limit() -> int:
    raw = request.args.get("limit", "20")
    try:
        value = int(raw)
    except ValueError as error:
        raise ValidationError("limit must be an integer.") from error
    if value < 1 or value > 100:
        raise ValidationError("limit must be between 1 and 100.")
    return value


def _datetime_arg(name: str, default: datetime) -> datetime:
    value = request.args.get(name)
    if not value:
        return default
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError(
            f"{name} must be an ISO 8601 datetime."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{name} must include a timezone offset.")
    return parsed.astimezone(timezone.utc)
