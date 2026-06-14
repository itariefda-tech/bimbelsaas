from uuid import UUID, uuid4

from app.extensions import db
from app.models.attendance import Attendance
from app.models.audit_log import AuditLog
from app.permissions.constants import Role, ScopeType


def _login(client, email, academy_id):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": email,
            "password": "very-secure-password",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['data']['access_token']}"}


def _identity_headers(
    client,
    create_identity,
    academy_id,
    *,
    email,
    role,
    scope_type,
    branch_id=None,
    scope_id=None,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email=email,
        assignments=(
            {
                "role": role,
                "scope_type": scope_type,
                "branch_id": branch_id,
                "scope_id": scope_id,
            },
        ),
    )
    return user, _login(client, user.email, academy_id)


def _post(client, path, headers, payload):
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 201
    return response.json["data"]


def _attendance_setup(
    client,
    create_identity,
    academy_id,
    branch_id,
    *,
    suffix,
    student_count=1,
):
    _, admin_headers = _identity_headers(
        client,
        create_identity,
        academy_id,
        email=f"attendance-admin-{suffix}@example.com",
        role=Role.BRANCH_ADMIN,
        scope_type=ScopeType.BRANCH,
        branch_id=branch_id,
    )
    academic_class = _post(
        client,
        f"/api/v1/branches/{branch_id}/classes",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "class_code": f"ATT-{suffix}",
            "class_name": f"Attendance {suffix}",
            "capacity": 10,
        },
    )
    teacher_user, teacher_headers = _identity_headers(
        client,
        create_identity,
        academy_id,
        email=f"attendance-teacher-{suffix}@example.com",
        role=Role.TEACHER,
        scope_type=ScopeType.ASSIGNED_CLASS,
        branch_id=branch_id,
        scope_id=UUID(academic_class["id"]),
    )
    teacher = _post(
        client,
        f"/api/v1/branches/{branch_id}/teachers",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "teacher_code": f"AT-{suffix}",
            "full_name": f"Attendance Teacher {suffix}",
            "user_id": str(teacher_user.id),
        },
    )
    room = _post(
        client,
        f"/api/v1/branches/{branch_id}/rooms",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "room_code": f"AR-{suffix}",
            "room_name": f"Attendance Room {suffix}",
            "capacity": 10,
        },
    )
    students = []
    for index in range(student_count):
        student = _post(
            client,
            f"/api/v1/branches/{branch_id}/students",
            admin_headers,
            {
                "academy_id": str(academy_id),
                "student_code": f"AS-{suffix}-{index}",
                "full_name": f"Attendance Student {suffix} {index}",
            },
        )
        enrolled = client.post(
            (
                f"/api/v1/branches/{branch_id}/classes/{academic_class['id']}"
                f"/students/{student['id']}"
            ),
            headers=admin_headers,
            json={"academy_id": str(academy_id)},
        )
        assert enrolled.status_code == 201
        students.append(student)
    schedule = _post(
        client,
        f"/api/v1/branches/{branch_id}/schedules",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "class_id": academic_class["id"],
            "teacher_id": teacher["id"],
            "room_id": room["id"],
            "starts_at": "2026-07-05T09:00:00+07:00",
            "ends_at": "2026-07-05T11:00:00+07:00",
            "timezone": "Asia/Jakarta",
        },
    )
    return {
        "admin_headers": admin_headers,
        "teacher_headers": teacher_headers,
        "class": academic_class,
        "students": students,
        "session_id": schedule["session"]["id"],
    }


def _save_attendance(
    client,
    headers,
    academy_id,
    branch_id,
    session_id,
    entries,
):
    return client.put(
        f"/api/v1/branches/{branch_id}/sessions/{session_id}/attendance",
        headers=headers,
        json={"academy_id": str(academy_id), "entries": entries},
    )


def test_teacher_can_save_and_finalize_complete_attendance(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _attendance_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        suffix="LIFECYCLE",
        student_count=2,
    )
    entries = [
        {
            "student_id": setup["students"][0]["id"],
            "attendance_status": "present",
        },
        {
            "student_id": setup["students"][1]["id"],
            "attendance_status": "online",
            "note": "Joined remotely",
        },
    ]
    saved = _save_attendance(
        client,
        setup["teacher_headers"],
        academy_id,
        branch_id,
        setup["session_id"],
        entries,
    )
    finalized = client.post(
        (
            f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
            "/attendance/finalize"
        ),
        headers=setup["teacher_headers"],
        json={"academy_id": str(academy_id)},
    )

    assert saved.status_code == 200
    assert len(saved.json["data"]["entries"]) == 2
    assert finalized.status_code == 200
    assert finalized.json["data"]["attendance_status"] == "finalized"
    assert AuditLog.query.filter_by(action_type="attendance.recorded").count() == 2
    assert AuditLog.query.filter_by(action_type="attendance.finalized").count() == 1


def test_finalization_requires_every_active_student(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _attendance_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        suffix="INCOMPLETE",
        student_count=2,
    )
    assert (
        _save_attendance(
            client,
            setup["teacher_headers"],
            academy_id,
            branch_id,
            setup["session_id"],
            [
                {
                    "student_id": setup["students"][0]["id"],
                    "attendance_status": "late",
                }
            ],
        ).status_code
        == 200
    )

    finalized = client.post(
        (
            f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
            "/attendance/finalize"
        ),
        headers=setup["teacher_headers"],
        json={"academy_id": str(academy_id)},
    )

    assert finalized.status_code == 409
    assert finalized.json["error"]["code"] == "attendance_incomplete"


def test_finalized_attendance_requires_reason_and_separate_approval(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _attendance_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        suffix="EDIT",
    )
    entry = {
        "student_id": setup["students"][0]["id"],
        "attendance_status": "present",
    }
    assert (
        _save_attendance(
            client,
            setup["teacher_headers"],
            academy_id,
            branch_id,
            setup["session_id"],
            [entry],
        ).status_code
        == 200
    )
    assert (
        client.post(
            (
                f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
                "/attendance/finalize"
            ),
            headers=setup["teacher_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    attendance = Attendance.query.one()
    direct_edit = _save_attendance(
        client,
        setup["teacher_headers"],
        academy_id,
        branch_id,
        setup["session_id"],
        [{**entry, "attendance_status": "excused"}],
    )
    missing_reason = client.post(
        (
            f"/api/v1/branches/{branch_id}/attendances/{attendance.id}"
            "/edit-requests"
        ),
        headers=setup["teacher_headers"],
        json={
            "academy_id": str(academy_id),
            "attendance_status": "excused",
        },
    )
    requested = client.post(
        (
            f"/api/v1/branches/{branch_id}/attendances/{attendance.id}"
            "/edit-requests"
        ),
        headers=setup["teacher_headers"],
        json={
            "academy_id": str(academy_id),
            "attendance_status": "excused",
            "note": "Medical documentation received",
            "reason": "Absence was excused after review",
        },
    )
    request_id = requested.json["data"]["id"]
    approved = client.post(
        (
            f"/api/v1/branches/{branch_id}/attendance-edit-requests/"
            f"{request_id}/approve"
        ),
        headers=setup["admin_headers"],
        json={
            "academy_id": str(academy_id),
            "reason": "Documentation verified",
        },
    )
    db.session.refresh(attendance)

    assert direct_edit.status_code == 409
    assert direct_edit.json["error"]["code"] == "attendance_finalized"
    assert missing_reason.status_code == 422
    assert requested.status_code == 201
    assert approved.status_code == 200
    assert attendance.attendance_status == "excused"
    assert approved.json["data"]["status"] == "approved"
    assert (
        AuditLog.query.filter_by(
            action_type="attendance.finalized_edit_applied"
        ).count()
        == 1
    )


def test_branch_admin_cannot_self_approve_finalized_edit(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _attendance_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        suffix="SELF",
    )
    assert (
        _save_attendance(
            client,
            setup["admin_headers"],
            academy_id,
            branch_id,
            setup["session_id"],
            [
                {
                    "student_id": setup["students"][0]["id"],
                    "attendance_status": "absent",
                }
            ],
        ).status_code
        == 200
    )
    assert (
        client.post(
            (
                f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
                "/attendance/finalize"
            ),
            headers=setup["admin_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    attendance = Attendance.query.one()
    requested = client.post(
        (
            f"/api/v1/branches/{branch_id}/attendances/{attendance.id}"
            "/edit-requests"
        ),
        headers=setup["admin_headers"],
        json={
            "academy_id": str(academy_id),
            "attendance_status": "present",
            "reason": "Administrative correction",
        },
    )
    approval = client.post(
        (
            f"/api/v1/branches/{branch_id}/attendance-edit-requests/"
            f"{requested.json['data']['id']}/approve"
        ),
        headers=setup["admin_headers"],
        json={"academy_id": str(academy_id), "reason": "Self review"},
    )

    assert requested.status_code == 201
    assert approval.status_code == 403
    assert (
        approval.json["error"]["code"]
        == "attendance_edit_self_approval_denied"
    )
def test_teacher_cannot_access_another_assigned_class_attendance(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _attendance_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        suffix="SCOPE",
    )
    _, other_headers = _identity_headers(
        client,
        create_identity,
        academy_id,
        email="attendance-other-teacher@example.com",
        role=Role.TEACHER,
        scope_type=ScopeType.ASSIGNED_CLASS,
        branch_id=branch_id,
        scope_id=uuid4(),
    )

    denied = client.get(
        (
            f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
            "/attendance"
        ),
        headers=other_headers,
    )

    assert denied.status_code == 403
    assert denied.json["error"]["code"] == "permission_denied"
