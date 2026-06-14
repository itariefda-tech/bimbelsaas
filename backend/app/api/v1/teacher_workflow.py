from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Blueprint, g, request

from app.common.errors import ValidationError
from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_string,
    required_string,
    required_uuid,
)
from app.permissions.decorators import require_auth
from app.services.attendance_service import AttendanceService
from app.services.branch_service import BranchService
from app.services.lesson_summary_service import LessonSummaryService
from app.services.teacher_dashboard_service import TeacherDashboardService

teacher_workflow_api = Blueprint("teacher_workflow", __name__)


@teacher_workflow_api.get("/teacher/dashboard")
@require_auth
def teacher_dashboard():
    academy_id = g.principal.user.academy_id
    if academy_id is None:
        raise ValidationError("A teacher academy is required.")
    timezone_name = request.args.get("timezone", "Asia/Jakarta").strip()
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ValidationError("Invalid IANA timezone.") from error
    date_value = request.args.get("date")
    if date_value:
        try:
            target_date = date.fromisoformat(date_value)
        except ValueError as error:
            raise ValidationError("date must use YYYY-MM-DD format.") from error
    else:
        target_date = datetime.now(zone).date()
    dashboard = TeacherDashboardService().daily_dashboard(
        g.principal,
        academy_id=academy_id,
        target_date=target_date,
        timezone_name=timezone_name,
    )
    return success_response(data=dashboard, message="Teacher dashboard loaded.")


@teacher_workflow_api.get(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/attendance"
)
@require_auth
def get_attendance(branch_id, session_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    sheet = AttendanceService().get_sheet(
        g.principal,
        academy_id=branch.academy_id,
        branch_id=branch_id,
        session_id=session_id,
    )
    return success_response(data=sheet, message="Attendance loaded.")


@teacher_workflow_api.put(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/attendance"
)
@require_auth
def save_attendance(branch_id, session_id):
    payload = json_payload()
    entries = _attendance_entries(payload.get("entries"))
    sheet = AttendanceService().save_draft(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        session_id=session_id,
        entries=entries,
    )
    return success_response(data=sheet, message="Attendance draft saved.")


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/attendance/finalize"
)
@require_auth
def finalize_attendance(branch_id, session_id):
    payload = json_payload()
    sheet = AttendanceService().finalize(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        session_id=session_id,
    )
    return success_response(data=sheet, message="Attendance finalized.")


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/attendances/<uuid:attendance_id>/edit-requests"
)
@require_auth
def request_attendance_edit(branch_id, attendance_id):
    payload = json_payload()
    request = AttendanceService().request_edit(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        attendance_id=attendance_id,
        proposed_status=required_string(payload, "attendance_status"),
        proposed_note=optional_string(payload, "note"),
        reason=required_string(payload, "reason"),
    )
    return success_response(
        data=AttendanceService.serialize_request(request),
        message="Attendance edit requested.",
        status=201,
    )


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/attendance-edit-requests/"
    "<uuid:request_id>/approve"
)
@require_auth
def approve_attendance_edit(branch_id, request_id):
    return _decide_attendance_edit(branch_id, request_id, approve=True)


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/attendance-edit-requests/"
    "<uuid:request_id>/reject"
)
@require_auth
def reject_attendance_edit(branch_id, request_id):
    return _decide_attendance_edit(branch_id, request_id, approve=False)


@teacher_workflow_api.get(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/lesson-summary"
)
@require_auth
def get_lesson_summary(branch_id, session_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    summary = LessonSummaryService().get_for_session(
        g.principal,
        academy_id=branch.academy_id,
        branch_id=branch_id,
        session_id=session_id,
    )
    return success_response(
        data=LessonSummaryService.serialize(summary) if summary else None,
        message="Lesson summary loaded.",
    )


@teacher_workflow_api.put(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/lesson-summary"
)
@require_auth
def save_lesson_summary(branch_id, session_id):
    payload = json_payload()
    summary = LessonSummaryService().save_draft(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        session_id=session_id,
        content=_lesson_summary_content(payload),
    )
    return success_response(
        data=LessonSummaryService.serialize(summary),
        message="Lesson summary draft saved.",
    )


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/sessions/<uuid:session_id>/"
    "lesson-summary/publish"
)
@require_auth
def publish_lesson_summary(branch_id, session_id):
    payload = json_payload()
    summary = LessonSummaryService().publish(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        session_id=session_id,
    )
    return success_response(
        data=LessonSummaryService.serialize(summary),
        message="Lesson summary published.",
    )


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/lesson-summaries/<uuid:summary_id>/"
    "edit-requests"
)
@require_auth
def request_lesson_summary_edit(branch_id, summary_id):
    payload = json_payload()
    edit_request = LessonSummaryService().request_edit(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        summary_id=summary_id,
        content=_lesson_summary_content(payload),
        reason=required_string(payload, "reason"),
    )
    return success_response(
        data=LessonSummaryService.serialize_request(edit_request),
        message="Lesson summary edit requested.",
        status=201,
    )


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/lesson-summary-edit-requests/"
    "<uuid:request_id>/approve"
)
@require_auth
def approve_lesson_summary_edit(branch_id, request_id):
    return _decide_lesson_summary_edit(branch_id, request_id, approve=True)


@teacher_workflow_api.post(
    "/branches/<uuid:branch_id>/lesson-summary-edit-requests/"
    "<uuid:request_id>/reject"
)
@require_auth
def reject_lesson_summary_edit(branch_id, request_id):
    return _decide_lesson_summary_edit(branch_id, request_id, approve=False)


def _decide_attendance_edit(branch_id: UUID, request_id: UUID, *, approve: bool):
    payload = json_payload()
    request = AttendanceService().decide_edit(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        request_id=request_id,
        approve=approve,
        reason=required_string(payload, "reason"),
    )
    return success_response(
        data=AttendanceService.serialize_request(request),
        message=(
            "Attendance edit approved."
            if approve
            else "Attendance edit rejected."
        ),
    )


def _decide_lesson_summary_edit(
    branch_id: UUID,
    request_id: UUID,
    *,
    approve: bool,
):
    payload = json_payload()
    edit_request = LessonSummaryService().decide_edit(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        request_id=request_id,
        approve=approve,
        reason=required_string(payload, "reason"),
    )
    return success_response(
        data=LessonSummaryService.serialize_request(edit_request),
        message=(
            "Lesson summary edit approved."
            if approve
            else "Lesson summary edit rejected."
        ),
    )


def _lesson_summary_content(payload: dict) -> dict[str, str | None]:
    return {
        "lesson_topic": required_string(payload, "lesson_topic"),
        "class_summary": required_string(payload, "class_summary"),
        "teacher_notes": optional_string(payload, "teacher_notes"),
        "homework": optional_string(payload, "homework"),
        "student_attention_notes": optional_string(
            payload,
            "student_attention_notes",
        ),
    }


def _attendance_entries(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise ValidationError(
            "entries must be a non-empty list.",
            details={"entries": "required"},
        )
    entries = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError(f"entries[{index}] must be an object.")
        status = item.get("attendance_status")
        if not isinstance(status, str) or not status.strip():
            raise ValidationError(
                f"entries[{index}].attendance_status is required."
            )
        note = item.get("note")
        if note is not None and not isinstance(note, str):
            raise ValidationError(f"entries[{index}].note must be a string.")
        entries.append(
            {
                "student_id": required_uuid(
                    item.get("student_id"),
                    f"entries[{index}].student_id",
                ),
                "attendance_status": status.strip(),
                "note": note.strip() if isinstance(note, str) else None,
            }
        )
    return entries
