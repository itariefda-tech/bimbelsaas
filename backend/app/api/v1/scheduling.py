from flask import Blueprint, g

from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_string,
    required_datetime,
    required_positive_int,
    required_string,
    required_uuid,
    string_value,
)
from app.permissions.decorators import require_auth
from app.services.class_service import ClassService
from app.services.branch_service import BranchService
from app.services.room_service import RoomService
from app.services.reschedule_service import RescheduleService
from app.services.schedule_service import ScheduleService

scheduling_api = Blueprint("scheduling", __name__)


@scheduling_api.get("/branches/<uuid:branch_id>/classes")
@require_auth
def list_classes(branch_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    classes = ClassService().list_for_branch(
        g.principal,
        branch.academy_id,
        branch_id,
    )
    return success_response(
        data=[ClassService.serialize(item) for item in classes],
        message="Classes loaded.",
    )


@scheduling_api.post("/branches/<uuid:branch_id>/classes")
@require_auth
def create_class(branch_id):
    payload = json_payload()
    academic_class = ClassService().create(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_code=required_string(payload, "class_code"),
        class_name=required_string(payload, "class_name"),
        capacity=required_positive_int(payload, "capacity"),
    )
    return success_response(
        data=ClassService.serialize(academic_class),
        message="Class created.",
        status=201,
    )


@scheduling_api.post(
    "/branches/<uuid:branch_id>/classes/<uuid:class_id>/students/<uuid:student_id>"
)
@require_auth
def enroll_student(branch_id, class_id, student_id):
    payload = json_payload()
    enrollment = ClassService().enroll_student(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=class_id,
        student_id=student_id,
    )
    return success_response(
        data={
            "id": str(enrollment.id),
            "class_id": str(enrollment.class_id),
            "student_id": str(enrollment.student_id),
            "enrollment_status": enrollment.enrollment_status,
        },
        message="Student enrolled.",
        status=201,
    )


@scheduling_api.get("/branches/<uuid:branch_id>/rooms")
@require_auth
def list_rooms(branch_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    rooms = RoomService().list_for_branch(
        g.principal,
        branch.academy_id,
        branch_id,
    )
    return success_response(
        data=[RoomService.serialize(room) for room in rooms],
        message="Rooms loaded.",
    )


@scheduling_api.post("/branches/<uuid:branch_id>/rooms")
@require_auth
def create_room(branch_id):
    payload = json_payload()
    room = RoomService().create(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        room_code=required_string(payload, "room_code"),
        room_name=required_string(payload, "room_name"),
        capacity=required_positive_int(payload, "capacity"),
        room_type=optional_string(payload, "room_type"),
    )
    return success_response(
        data=RoomService.serialize(room),
        message="Room created.",
        status=201,
    )


@scheduling_api.get("/branches/<uuid:branch_id>/schedules")
@require_auth
def list_schedules(branch_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    schedules = ScheduleService().list_for_branch(
        g.principal,
        branch.academy_id,
        branch_id,
    )
    return success_response(
        data=[ScheduleService.serialize(item) for item in schedules],
        message="Schedules loaded.",
    )


@scheduling_api.post("/branches/<uuid:branch_id>/schedules")
@require_auth
def create_schedule(branch_id):
    payload = json_payload()
    schedule = ScheduleService().create(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        class_id=required_uuid(payload.get("class_id"), "class_id"),
        teacher_id=required_uuid(payload.get("teacher_id"), "teacher_id"),
        room_id=required_uuid(payload.get("room_id"), "room_id"),
        starts_at=required_datetime(payload.get("starts_at"), "starts_at"),
        ends_at=required_datetime(payload.get("ends_at"), "ends_at"),
        timezone_name=string_value(payload, "timezone", "Asia/Jakarta"),
        status=string_value(payload, "status", "scheduled"),
    )
    return success_response(
        data=ScheduleService.serialize(schedule),
        message="Schedule created.",
        status=201,
    )


@scheduling_api.patch(
    "/branches/<uuid:branch_id>/schedules/<uuid:schedule_id>/status"
)
@require_auth
def transition_schedule(branch_id, schedule_id):
    payload = json_payload()
    schedule = ScheduleService().transition(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        schedule_id=schedule_id,
        target_status=required_string(payload, "status"),
        reason=optional_string(payload, "reason"),
    )
    return success_response(
        data=ScheduleService.serialize(schedule),
        message="Schedule status updated.",
    )


@scheduling_api.get(
    "/branches/<uuid:branch_id>/schedules/<uuid:schedule_id>/reschedule-requests"
)
@require_auth
def list_reschedule_requests(branch_id, schedule_id):
    branch = BranchService().get_visible(g.principal, branch_id)
    requests = RescheduleService().list_for_schedule(
        g.principal,
        academy_id=branch.academy_id,
        branch_id=branch_id,
        schedule_id=schedule_id,
    )
    return success_response(
        data=[RescheduleService.serialize(item) for item in requests],
        message="Reschedule requests loaded.",
    )


@scheduling_api.post(
    "/branches/<uuid:branch_id>/schedules/<uuid:schedule_id>/reschedule-requests"
)
@require_auth
def request_reschedule(branch_id, schedule_id):
    payload = json_payload()
    change = RescheduleService().request(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        schedule_id=schedule_id,
        teacher_id=required_uuid(payload.get("teacher_id"), "teacher_id"),
        room_id=required_uuid(payload.get("room_id"), "room_id"),
        starts_at=required_datetime(payload.get("starts_at"), "starts_at"),
        ends_at=required_datetime(payload.get("ends_at"), "ends_at"),
        timezone_name=string_value(payload, "timezone", "Asia/Jakarta"),
        reason=required_string(payload, "reason"),
    )
    return success_response(
        data=RescheduleService.serialize(change),
        message="Reschedule requested.",
        status=201,
    )


@scheduling_api.post(
    "/branches/<uuid:branch_id>/reschedule-requests/<uuid:request_id>/approve"
)
@require_auth
def approve_reschedule(branch_id, request_id):
    payload = json_payload()
    change = RescheduleService().approve(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        request_id=request_id,
        decision_reason=required_string(payload, "reason"),
    )
    return success_response(
        data=RescheduleService.serialize(change),
        message="Reschedule approved.",
    )


@scheduling_api.post(
    "/branches/<uuid:branch_id>/reschedule-requests/<uuid:request_id>/reject"
)
@require_auth
def reject_reschedule(branch_id, request_id):
    payload = json_payload()
    change = RescheduleService().reject(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=branch_id,
        request_id=request_id,
        decision_reason=required_string(payload, "reason"),
    )
    return success_response(
        data=RescheduleService.serialize(change),
        message="Reschedule rejected.",
    )
