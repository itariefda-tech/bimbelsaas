from flask import Blueprint, g

from app.common.responses import success_response
from app.common.validation import (
    json_payload,
    optional_date,
    optional_string,
    optional_uuid,
    required_string,
    required_uuid,
    string_value,
)
from app.permissions.decorators import require_auth
from app.services.student_service import StudentService
from app.services.teacher_service import TeacherService

people_api = Blueprint("people", __name__)


@people_api.get("/academies/<uuid:academy_id>/teachers")
@require_auth
def list_teachers(academy_id):
    teachers = TeacherService().list_visible(g.principal, academy_id)
    return success_response(
        data=[TeacherService.serialize(teacher) for teacher in teachers],
        message="Teachers loaded.",
    )


@people_api.post("/branches/<uuid:branch_id>/teachers")
@require_auth
def create_teacher(branch_id):
    payload = json_payload()
    academy_id = required_uuid(payload.get("academy_id"), "academy_id")
    teacher = TeacherService().create(
        g.principal,
        academy_id=academy_id,
        initial_branch_id=branch_id,
        teacher_code=required_string(payload, "teacher_code"),
        full_name=required_string(payload, "full_name"),
        employment_status=string_value(
            payload,
            "employment_status",
            "active",
        ),
        specialization=optional_string(payload, "specialization"),
        user_id=optional_uuid(payload.get("user_id"), "user_id"),
    )
    return success_response(
        data=TeacherService.serialize(teacher),
        message="Teacher created.",
        status=201,
    )


@people_api.get("/academies/<uuid:academy_id>/teachers/<uuid:teacher_id>")
@require_auth
def get_teacher(academy_id, teacher_id):
    teacher = TeacherService().get_visible(g.principal, academy_id, teacher_id)
    return success_response(
        data=TeacherService.serialize(teacher),
        message="Teacher loaded.",
    )


@people_api.patch("/academies/<uuid:academy_id>/teachers/<uuid:teacher_id>")
@require_auth
def update_teacher(academy_id, teacher_id):
    payload = json_payload(require_nonempty=True)
    if "user_id" in payload:
        payload["user_id"] = optional_uuid(payload["user_id"], "user_id")
    teacher = TeacherService().update(
        g.principal,
        academy_id,
        teacher_id,
        payload,
    )
    return success_response(
        data=TeacherService.serialize(teacher),
        message="Teacher updated.",
    )


@people_api.delete("/academies/<uuid:academy_id>/teachers/<uuid:teacher_id>")
@require_auth
def archive_teacher(academy_id, teacher_id):
    teacher = TeacherService().archive(
        g.principal,
        academy_id,
        teacher_id,
    )
    return success_response(
        data=TeacherService.serialize(teacher),
        message="Teacher archived.",
    )


@people_api.post(
    "/academies/<uuid:academy_id>/teachers/<uuid:teacher_id>/branches/<uuid:branch_id>"
)
@require_auth
def assign_teacher_branch(academy_id, teacher_id, branch_id):
    assignment = TeacherService().assign_branch(
        g.principal,
        academy_id,
        teacher_id,
        branch_id,
    )
    return success_response(
        data={
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "branch_id": str(assignment.branch_id),
            "assignment_status": assignment.assignment_status,
        },
        message="Teacher assigned to branch.",
        status=201,
    )


@people_api.delete(
    "/academies/<uuid:academy_id>/teachers/<uuid:teacher_id>/branches/<uuid:branch_id>"
)
@require_auth
def remove_teacher_branch(academy_id, teacher_id, branch_id):
    assignment = TeacherService().remove_branch(
        g.principal,
        academy_id,
        teacher_id,
        branch_id,
    )
    return success_response(
        data={
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "branch_id": str(assignment.branch_id),
            "assignment_status": assignment.assignment_status,
        },
        message="Teacher removed from branch.",
    )


@people_api.get("/academies/<uuid:academy_id>/students")
@require_auth
def list_students(academy_id):
    students = StudentService().list_visible(g.principal, academy_id)
    return success_response(
        data=[StudentService.serialize(student) for student in students],
        message="Students loaded.",
    )


@people_api.post("/branches/<uuid:branch_id>/students")
@require_auth
def create_student(branch_id):
    payload = json_payload()
    academy_id = required_uuid(payload.get("academy_id"), "academy_id")
    student = StudentService().create(
        g.principal,
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code=required_string(payload, "student_code"),
        full_name=required_string(payload, "full_name"),
        birth_date=optional_date(payload.get("birth_date"), "birth_date"),
        user_id=optional_uuid(payload.get("user_id"), "user_id"),
    )
    return success_response(
        data=StudentService.serialize(student),
        message="Student created.",
        status=201,
    )


@people_api.get("/academies/<uuid:academy_id>/students/<uuid:student_id>")
@require_auth
def get_student(academy_id, student_id):
    student = StudentService().get_visible(g.principal, academy_id, student_id)
    return success_response(
        data=StudentService.serialize(student),
        message="Student loaded.",
    )


@people_api.patch("/academies/<uuid:academy_id>/students/<uuid:student_id>")
@require_auth
def update_student(academy_id, student_id):
    payload = json_payload(require_nonempty=True)
    if "birth_date" in payload:
        payload["birth_date"] = optional_date(payload["birth_date"], "birth_date")
    if "home_branch_id" in payload:
        payload["home_branch_id"] = required_uuid(
            payload["home_branch_id"],
            "home_branch_id",
        )
    if "user_id" in payload:
        payload["user_id"] = optional_uuid(payload["user_id"], "user_id")
    student = StudentService().update(
        g.principal,
        academy_id,
        student_id,
        payload,
    )
    return success_response(
        data=StudentService.serialize(student),
        message="Student updated.",
    )


@people_api.delete("/academies/<uuid:academy_id>/students/<uuid:student_id>")
@require_auth
def archive_student(academy_id, student_id):
    student = StudentService().archive(g.principal, academy_id, student_id)
    return success_response(
        data=StudentService.serialize(student),
        message="Student archived.",
    )


@people_api.get(
    "/academies/<uuid:academy_id>/students/<uuid:student_id>/branch-access/<uuid:branch_id>"
)
@require_auth
def student_branch_access(academy_id, student_id, branch_id):
    service = StudentService()
    service.get_visible(g.principal, academy_id, student_id)
    allowed = service.can_access_branch(academy_id, student_id, branch_id)
    return success_response(
        data={
            "student_id": str(student_id),
            "branch_id": str(branch_id),
            "allowed": allowed,
            "source": "home_branch" if allowed else "default_deny",
        },
        message="Student branch access evaluated.",
    )
