from uuid import UUID

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.class_student import ClassStudent
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


def _director(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="schedule-director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _manager(client, create_identity, academy_id, branch_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="schedule-manager@example.com",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _admin(client, create_identity, academy_id, branch_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="schedule-admin@example.com",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _create_class(client, headers, academy_id, branch_id, suffix):
    response = client.post(
        f"/api/v1/branches/{branch_id}/classes",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "class_code": f"C-{suffix}",
            "class_name": f"Class {suffix}",
            "capacity": 10,
        },
    )
    assert response.status_code == 201
    return response.json["data"]


def _create_room(client, headers, academy_id, branch_id, suffix):
    response = client.post(
        f"/api/v1/branches/{branch_id}/rooms",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "room_code": f"R-{suffix}",
            "room_name": f"Room {suffix}",
            "capacity": 10,
        },
    )
    assert response.status_code == 201
    return response.json["data"]


def _create_teacher(client, headers, academy_id, branch_id, suffix):
    response = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": f"T-{suffix}",
            "full_name": f"Teacher {suffix}",
        },
    )
    assert response.status_code == 201
    return response.json["data"]


def _create_student(client, headers, academy_id, branch_id, suffix):
    response = client.post(
        f"/api/v1/branches/{branch_id}/students",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "student_code": f"S-{suffix}",
            "full_name": f"Student {suffix}",
        },
    )
    assert response.status_code == 201
    return response.json["data"]


def _enroll(client, headers, academy_id, branch_id, class_id, student_id):
    response = client.post(
        f"/api/v1/branches/{branch_id}/classes/{class_id}/students/{student_id}",
        headers=headers,
        json={"academy_id": str(academy_id)},
    )
    assert response.status_code == 201


def _schedule(
    client,
    headers,
    academy_id,
    branch_id,
    academic_class,
    teacher,
    room,
    *,
    starts_at="2026-07-01T09:00:00+07:00",
    ends_at="2026-07-01T11:00:00+07:00",
):
    return client.post(
        f"/api/v1/branches/{branch_id}/schedules",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "class_id": academic_class["id"],
            "teacher_id": teacher["id"],
            "room_id": room["id"],
            "starts_at": starts_at,
            "ends_at": ends_at,
            "timezone": "Asia/Jakarta",
        },
    )


def test_schedule_creation_builds_session_and_audit_lifecycle(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    academic_class = _create_class(
        client, headers, academy_id, branch_id, "FOUNDATION"
    )
    room = _create_room(client, headers, academy_id, branch_id, "FOUNDATION")
    teacher = _create_teacher(
        client, headers, academy_id, branch_id, "FOUNDATION"
    )

    created = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        academic_class,
        teacher,
        room,
    )
    schedule = created.json["data"]
    transitioned = client.patch(
        f"/api/v1/branches/{branch_id}/schedules/{schedule['id']}/status",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "status": "confirmed",
            "reason": "Operational confirmation",
        },
    )

    assert created.status_code == 201
    assert schedule["session"]["status"] == "scheduled"
    assert transitioned.status_code == 200
    assert transitioned.json["data"]["status"] == "confirmed"
    assert transitioned.json["data"]["session"]["status"] == "confirmed"
    assert AuditLog.query.filter_by(action_type="schedule.created").count() == 1
    assert (
        AuditLog.query.filter_by(action_type="schedule.status_changed").count()
        == 1
    )


def test_teacher_conflict_short_circuits_before_room_conflict(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    first_class = _create_class(client, headers, academy_id, branch_id, "TC1")
    second_class = _create_class(client, headers, academy_id, branch_id, "TC2")
    room = _create_room(client, headers, academy_id, branch_id, "TC")
    teacher = _create_teacher(client, headers, academy_id, branch_id, "TC")
    assert _schedule(
        client, headers, academy_id, branch_id, first_class, teacher, room
    ).status_code == 201

    conflict = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        second_class,
        teacher,
        room,
        starts_at="2026-07-01T10:00:00+07:00",
        ends_at="2026-07-01T12:00:00+07:00",
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "teacher_schedule_conflict"
    assert conflict.json["error"]["details"]["stage"] == "teacher"


def test_room_conflict_runs_after_teacher_validation(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    first_class = _create_class(client, headers, academy_id, branch_id, "RC1")
    second_class = _create_class(client, headers, academy_id, branch_id, "RC2")
    room = _create_room(client, headers, academy_id, branch_id, "RC")
    first_teacher = _create_teacher(client, headers, academy_id, branch_id, "RC1")
    second_teacher = _create_teacher(client, headers, academy_id, branch_id, "RC2")
    assert _schedule(
        client, headers, academy_id, branch_id, first_class, first_teacher, room
    ).status_code == 201

    conflict = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        second_class,
        second_teacher,
        room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "room_schedule_conflict"
    assert conflict.json["error"]["details"]["stage"] == "room"


def test_student_overlap_is_blocked_across_different_classes(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    first_class = _create_class(client, headers, academy_id, branch_id, "SC1")
    second_class = _create_class(client, headers, academy_id, branch_id, "SC2")
    first_room = _create_room(client, headers, academy_id, branch_id, "SC1")
    second_room = _create_room(client, headers, academy_id, branch_id, "SC2")
    first_teacher = _create_teacher(client, headers, academy_id, branch_id, "SC1")
    second_teacher = _create_teacher(client, headers, academy_id, branch_id, "SC2")
    student = _create_student(client, headers, academy_id, branch_id, "SC")
    _enroll(
        client, headers, academy_id, branch_id, first_class["id"], student["id"]
    )
    _enroll(
        client, headers, academy_id, branch_id, second_class["id"], student["id"]
    )
    assert _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        first_class,
        first_teacher,
        first_room,
    ).status_code == 201

    conflict = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        second_class,
        second_teacher,
        second_room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "student_schedule_conflict"
    assert conflict.json["error"]["details"]["stage"] == "student"


def test_same_class_time_conflict_runs_after_resource_checks(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    academic_class = _create_class(client, headers, academy_id, branch_id, "TIME")
    first_room = _create_room(client, headers, academy_id, branch_id, "TIME1")
    second_room = _create_room(client, headers, academy_id, branch_id, "TIME2")
    first_teacher = _create_teacher(
        client, headers, academy_id, branch_id, "TIME1"
    )
    second_teacher = _create_teacher(
        client, headers, academy_id, branch_id, "TIME2"
    )
    assert _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        academic_class,
        first_teacher,
        first_room,
    ).status_code == 201

    conflict = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        academic_class,
        second_teacher,
        second_room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "class_schedule_conflict"
    assert conflict.json["error"]["details"]["stage"] == "time"


def test_teacher_must_be_assigned_to_schedule_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    other_branch = create_branch(academy_id=academy_id, name="Schedule Branch")
    academic_class = _create_class(
        client, headers, academy_id, other_branch.id, "BRANCH"
    )
    room = _create_room(client, headers, academy_id, other_branch.id, "BRANCH")
    teacher = _create_teacher(
        client, headers, academy_id, branch_id, "HOMEONLY"
    )

    conflict = _schedule(
        client,
        headers,
        academy_id,
        other_branch.id,
        academic_class,
        teacher,
        room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "teacher_branch_not_assigned"
    assert conflict.json["error"]["details"]["stage"] == "teacher"


def test_class_from_another_branch_fails_at_branch_stage(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    other_branch = create_branch(academy_id=academy_id, name="Scoped Branch")
    wrong_class = _create_class(
        client, headers, academy_id, branch_id, "WRONG-BRANCH"
    )
    room = _create_room(
        client, headers, academy_id, other_branch.id, "SCOPED-BRANCH"
    )
    teacher = _create_teacher(
        client, headers, academy_id, other_branch.id, "SCOPED-BRANCH"
    )

    conflict = _schedule(
        client,
        headers,
        academy_id,
        other_branch.id,
        wrong_class,
        teacher,
        room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "class_not_active"
    assert conflict.json["error"]["details"]["stage"] == "branch"


def test_pipeline_denies_student_without_cross_branch_entitlement(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    other_branch = create_branch(academy_id=academy_id, name="Premium Branch")
    academic_class = _create_class(
        client, headers, academy_id, other_branch.id, "PREMIUM"
    )
    room = _create_room(client, headers, academy_id, other_branch.id, "PREMIUM")
    teacher = _create_teacher(
        client, headers, academy_id, other_branch.id, "PREMIUM"
    )
    student = _create_student(client, headers, academy_id, branch_id, "HOME")
    db.session.add(
        ClassStudent(
            academy_id=academy_id,
            branch_id=other_branch.id,
            class_id=UUID(academic_class["id"]),
            student_id=UUID(student["id"]),
            enrolled_by=None,
        )
    )
    db.session.commit()

    conflict = _schedule(
        client,
        headers,
        academy_id,
        other_branch.id,
        academic_class,
        teacher,
        room,
    )

    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "student_cross_branch_denied"
    assert conflict.json["error"]["details"]["stage"] == "cross_branch"


def test_branch_manager_cannot_manage_another_branch_schedule(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Schedule Branch")
    director_headers = _director(client, create_identity, academy_id)
    manager_headers = _manager(client, create_identity, academy_id, branch_id)

    denied = client.post(
        f"/api/v1/branches/{other_branch.id}/classes",
        headers=manager_headers,
        json={
            "academy_id": str(academy_id),
            "class_code": "DENIED",
            "class_name": "Denied Class",
            "capacity": 10,
        },
    )
    visible = client.get(
        f"/api/v1/branches/{other_branch.id}/schedules",
        headers=manager_headers,
    )
    allowed = _create_class(
        client, director_headers, academy_id, other_branch.id, "DIRECTOR"
    )

    assert denied.status_code == 403
    assert visible.status_code == 403
    assert allowed["branch_id"] == str(other_branch.id)


def test_schedule_requires_aware_valid_time_interval(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    academic_class = _create_class(client, headers, academy_id, branch_id, "TZ")
    room = _create_room(client, headers, academy_id, branch_id, "TZ")
    teacher = _create_teacher(client, headers, academy_id, branch_id, "TZ")

    response = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        academic_class,
        teacher,
        room,
        starts_at="2026-07-01T11:00:00",
        ends_at="2026-07-01T09:00:00+07:00",
    )

    assert response.status_code == 422
    assert response.json["error"]["code"] == "validation_error"


def _request_reschedule(
    client,
    headers,
    academy_id,
    branch_id,
    schedule_id,
    teacher_id,
    room_id,
    *,
    starts_at="2026-07-02T09:00:00+07:00",
    ends_at="2026-07-02T11:00:00+07:00",
    reason="Teacher is unavailable",
):
    payload = {
        "academy_id": str(academy_id),
        "teacher_id": teacher_id,
        "room_id": room_id,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "timezone": "Asia/Jakarta",
    }
    if reason is not None:
        payload["reason"] = reason
    return client.post(
        (
            f"/api/v1/branches/{branch_id}/schedules/{schedule_id}"
            "/reschedule-requests"
        ),
        headers=headers,
        json=payload,
    )


def test_reschedule_requires_reason_and_keeps_one_immutable_pending_request(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    academic_class = _create_class(client, headers, academy_id, branch_id, "RSN")
    room = _create_room(client, headers, academy_id, branch_id, "RSN")
    teacher = _create_teacher(client, headers, academy_id, branch_id, "RSN")
    schedule = _schedule(
        client, headers, academy_id, branch_id, academic_class, teacher, room
    ).json["data"]

    missing_reason = _request_reschedule(
        client,
        headers,
        academy_id,
        branch_id,
        schedule["id"],
        teacher["id"],
        room["id"],
        reason=None,
    )
    created = _request_reschedule(
        client,
        headers,
        academy_id,
        branch_id,
        schedule["id"],
        teacher["id"],
        room["id"],
    )
    duplicate = _request_reschedule(
        client,
        headers,
        academy_id,
        branch_id,
        schedule["id"],
        teacher["id"],
        room["id"],
        starts_at="2026-07-03T09:00:00+07:00",
        ends_at="2026-07-03T11:00:00+07:00",
    )

    assert missing_reason.status_code == 422
    assert created.status_code == 201
    assert created.json["data"]["original"]["starts_at"] == schedule["starts_at"]
    assert duplicate.status_code == 409
    assert duplicate.json["error"]["code"] == "pending_reschedule_exists"
    assert (
        AuditLog.query.filter_by(
            action_type="schedule.reschedule_requested"
        ).count()
        == 1
    )


def test_reschedule_approval_preserves_original_and_creates_replacement(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    admin_headers = _admin(client, create_identity, academy_id, branch_id)
    academic_class = _create_class(
        client, admin_headers, academy_id, branch_id, "APPROVE"
    )
    room = _create_room(client, admin_headers, academy_id, branch_id, "APPROVE")
    teacher = _create_teacher(
        client, admin_headers, academy_id, branch_id, "APPROVE"
    )
    schedule = _schedule(
        client,
        admin_headers,
        academy_id,
        branch_id,
        academic_class,
        teacher,
        room,
    ).json["data"]
    requested = _request_reschedule(
        client,
        admin_headers,
        academy_id,
        branch_id,
        schedule["id"],
        teacher["id"],
        room["id"],
    )
    request_id = requested.json["data"]["id"]

    self_approval = client.post(
        f"/api/v1/branches/{branch_id}/reschedule-requests/{request_id}/approve",
        headers=admin_headers,
        json={"academy_id": str(academy_id), "reason": "Reviewed"},
    )
    manager_headers = _manager(client, create_identity, academy_id, branch_id)
    approved = client.post(
        f"/api/v1/branches/{branch_id}/reschedule-requests/{request_id}/approve",
        headers=manager_headers,
        json={"academy_id": str(academy_id), "reason": "Operationally approved"},
    )
    schedules = client.get(
        f"/api/v1/branches/{branch_id}/schedules",
        headers=manager_headers,
    ).json["data"]
    original = next(item for item in schedules if item["id"] == schedule["id"])
    replacement_id = approved.json["data"]["replacement_schedule_id"]
    replacement = next(item for item in schedules if item["id"] == replacement_id)

    assert self_approval.status_code == 403
    assert (
        self_approval.json["error"]["code"]
        == "reschedule_self_approval_denied"
    )
    assert approved.status_code == 200
    assert approved.json["data"]["status"] == "approved"
    assert original["status"] == "rescheduled"
    assert original["starts_at"] == schedule["starts_at"]
    assert replacement["starts_at"].startswith("2026-07-02T02:00:00")
    assert len(schedules) == 2
    assert AuditLog.query.filter_by(action_type="schedule.rescheduled").count() == 1
    assert (
        AuditLog.query.filter_by(
            action_type="schedule.created_from_reschedule"
        ).count()
        == 1
    )


def test_approval_revalidates_conflicts_created_after_request(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _admin(client, create_identity, academy_id, branch_id)
    original_class = _create_class(client, headers, academy_id, branch_id, "RV1")
    conflict_class = _create_class(client, headers, academy_id, branch_id, "RV2")
    original_room = _create_room(client, headers, academy_id, branch_id, "RV1")
    conflict_room = _create_room(client, headers, academy_id, branch_id, "RV2")
    teacher = _create_teacher(client, headers, academy_id, branch_id, "RV")
    other_teacher = _create_teacher(client, headers, academy_id, branch_id, "RV2")
    original = _schedule(
        client,
        headers,
        academy_id,
        branch_id,
        original_class,
        teacher,
        original_room,
    ).json["data"]
    requested = _request_reschedule(
        client,
        headers,
        academy_id,
        branch_id,
        original["id"],
        teacher["id"],
        conflict_room["id"],
    )
    assert requested.status_code == 201
    assert (
        _schedule(
            client,
            headers,
            academy_id,
            branch_id,
            conflict_class,
            other_teacher,
            conflict_room,
            starts_at="2026-07-02T09:00:00+07:00",
            ends_at="2026-07-02T11:00:00+07:00",
        ).status_code
        == 201
    )

    approval = client.post(
        (
            f"/api/v1/branches/{branch_id}/reschedule-requests/"
            f"{requested.json['data']['id']}/approve"
        ),
        headers=_manager(client, create_identity, academy_id, branch_id),
        json={"academy_id": str(academy_id), "reason": "Approved after review"},
    )

    assert approval.status_code == 409
    assert approval.json["error"]["code"] == "room_schedule_conflict"
    assert approval.json["error"]["details"]["stage"] == "room"
    schedules = client.get(
        f"/api/v1/branches/{branch_id}/schedules",
        headers=headers,
    ).json["data"]
    unchanged = next(item for item in schedules if item["id"] == original["id"])
    assert unchanged["status"] == "scheduled"
