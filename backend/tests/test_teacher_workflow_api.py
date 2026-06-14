from uuid import UUID

from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.lesson_summary import LessonSummary
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


def _identity(
    client,
    create_identity,
    academy_id,
    email,
    assignments,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email=email,
        assignments=assignments,
    )
    return user, _login(client, email, academy_id)


def _post(client, path, headers, payload):
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 201
    return response.json["data"]


def _create_class(client, headers, academy_id, branch_id, suffix):
    return _post(
        client,
        f"/api/v1/branches/{branch_id}/classes",
        headers,
        {
            "academy_id": str(academy_id),
            "class_code": f"WF-{suffix}",
            "class_name": f"Workflow {suffix}",
            "capacity": 10,
        },
    )


def _create_room(client, headers, academy_id, branch_id, suffix):
    return _post(
        client,
        f"/api/v1/branches/{branch_id}/rooms",
        headers,
        {
            "academy_id": str(academy_id),
            "room_code": f"WR-{suffix}",
            "room_name": f"Workflow Room {suffix}",
            "capacity": 10,
        },
    )


def _create_schedule(
    client,
    headers,
    academy_id,
    branch_id,
    academic_class,
    teacher,
    room,
    starts_at,
    ends_at,
):
    return _post(
        client,
        f"/api/v1/branches/{branch_id}/schedules",
        headers,
        {
            "academy_id": str(academy_id),
            "class_id": academic_class["id"],
            "teacher_id": teacher["id"],
            "room_id": room["id"],
            "starts_at": starts_at,
            "ends_at": ends_at,
            "timezone": "Asia/Jakarta",
        },
    )


def _single_session_setup(
    client,
    create_identity,
    academy_id,
    branch_id,
    suffix,
):
    _, admin_headers = _identity(
        client,
        create_identity,
        academy_id,
        f"workflow-admin-{suffix}@example.com",
        (
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    academic_class = _create_class(
        client,
        admin_headers,
        academy_id,
        branch_id,
        suffix,
    )
    teacher_user, teacher_headers = _identity(
        client,
        create_identity,
        academy_id,
        f"workflow-teacher-{suffix}@example.com",
        (
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": branch_id,
                "scope_id": UUID(academic_class["id"]),
            },
        ),
    )
    teacher = _post(
        client,
        f"/api/v1/branches/{branch_id}/teachers",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "teacher_code": f"WT-{suffix}",
            "full_name": f"Workflow Teacher {suffix}",
            "user_id": str(teacher_user.id),
        },
    )
    room = _create_room(
        client,
        admin_headers,
        academy_id,
        branch_id,
        suffix,
    )
    schedule = _create_schedule(
        client,
        admin_headers,
        academy_id,
        branch_id,
        academic_class,
        teacher,
        room,
        "2026-07-05T09:00:00+07:00",
        "2026-07-05T11:00:00+07:00",
    )
    return {
        "admin_headers": admin_headers,
        "teacher_headers": teacher_headers,
        "class": academic_class,
        "teacher": teacher,
        "session_id": schedule["session"]["id"],
    }


def _summary_payload(academy_id, topic="Fractions", summary="Covered basics"):
    return {
        "academy_id": str(academy_id),
        "lesson_topic": topic,
        "class_summary": summary,
        "teacher_notes": "Good participation",
        "homework": "Exercise 1-5",
        "student_attention_notes": "Review denominator rules",
    }


def test_teacher_dashboard_lists_own_multi_branch_timeline_only(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Second Workflow")
    _, admin_headers = _identity(
        client,
        create_identity,
        academy_id,
        "dashboard-admin@example.com",
        (
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    first_class = _create_class(
        client, admin_headers, academy_id, branch_id, "DASH1"
    )
    second_class = _create_class(
        client, admin_headers, academy_id, other_branch.id, "DASH2"
    )
    teacher_user, teacher_headers = _identity(
        client,
        create_identity,
        academy_id,
        "dashboard-teacher@example.com",
        (
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": branch_id,
                "scope_id": UUID(first_class["id"]),
            },
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": other_branch.id,
                "scope_id": UUID(second_class["id"]),
            },
        ),
    )
    teacher = _post(
        client,
        f"/api/v1/branches/{branch_id}/teachers",
        admin_headers,
        {
            "academy_id": str(academy_id),
            "teacher_code": "WT-DASH",
            "full_name": "Dashboard Teacher",
            "user_id": str(teacher_user.id),
        },
    )
    assigned = client.post(
        (
            f"/api/v1/academies/{academy_id}/teachers/{teacher['id']}"
            f"/branches/{other_branch.id}"
        ),
        headers=admin_headers,
    )
    assert assigned.status_code == 201
    first_room = _create_room(
        client, admin_headers, academy_id, branch_id, "DASH1"
    )
    second_room = _create_room(
        client, admin_headers, academy_id, other_branch.id, "DASH2"
    )
    first = _create_schedule(
        client,
        admin_headers,
        academy_id,
        branch_id,
        first_class,
        teacher,
        first_room,
        "2026-07-05T08:00:00+07:00",
        "2026-07-05T10:00:00+07:00",
    )
    second = _create_schedule(
        client,
        admin_headers,
        academy_id,
        other_branch.id,
        second_class,
        teacher,
        second_room,
        "2026-07-05T13:00:00+07:00",
        "2026-07-05T15:00:00+07:00",
    )

    dashboard = client.get(
        "/api/v1/teacher/dashboard?date=2026-07-05&timezone=Asia/Jakarta",
        headers=teacher_headers,
    )
    data = dashboard.json["data"]

    assert dashboard.status_code == 200
    assert [item["session_id"] for item in data["timeline"]] == [
        first["session"]["id"],
        second["session"]["id"],
    ]
    assert {item["branch"]["id"] for item in data["timeline"]} == {
        str(branch_id),
        str(other_branch.id),
    }
    assert data["timeline"][0]["attendance_status"] == "draft"
    assert data["timeline"][0]["lesson_summary_status"] == "missing"
    assert data["timeline"][0]["shortcuts"]["attendance"].endswith(
        "/attendance"
    )


def test_lesson_summary_draft_publish_and_approved_edit(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _single_session_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        "SUMMARY",
    )
    path = (
        f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
        "/lesson-summary"
    )
    draft = client.put(
        path,
        headers=setup["teacher_headers"],
        json=_summary_payload(academy_id),
    )
    updated = client.put(
        path,
        headers=setup["teacher_headers"],
        json=_summary_payload(academy_id, summary="Covered advanced examples"),
    )
    published = client.post(
        f"{path}/publish",
        headers=setup["teacher_headers"],
        json={"academy_id": str(academy_id)},
    )
    summary_id = published.json["data"]["id"]
    direct_edit = client.put(
        path,
        headers=setup["teacher_headers"],
        json=_summary_payload(academy_id, summary="Silent overwrite"),
    )
    requested = client.post(
        (
            f"/api/v1/branches/{branch_id}/lesson-summaries/{summary_id}"
            "/edit-requests"
        ),
        headers=setup["teacher_headers"],
        json={
            **_summary_payload(
                academy_id,
                summary="Corrected published summary",
            ),
            "reason": "Clarify the covered material",
        },
    )
    approved = client.post(
        (
            f"/api/v1/branches/{branch_id}/lesson-summary-edit-requests/"
            f"{requested.json['data']['id']}/approve"
        ),
        headers=setup["admin_headers"],
        json={
            "academy_id": str(academy_id),
            "reason": "Correction verified",
        },
    )
    summary = db.session.get(LessonSummary, UUID(summary_id))

    assert draft.status_code == 200
    assert updated.json["data"]["class_summary"] == "Covered advanced examples"
    assert published.json["data"]["status"] == "published"
    assert direct_edit.status_code == 409
    assert direct_edit.json["error"]["code"] == "lesson_summary_published"
    assert requested.status_code == 201
    assert approved.json["data"]["status"] == "approved"
    assert summary.class_summary == "Corrected published summary"
    assert AuditLog.query.filter_by(action_type="lesson_summary.published").count() == 1
    assert (
        AuditLog.query.filter_by(
            action_type="lesson_summary.published_edit_applied"
        ).count()
        == 1
    )


def test_non_assigned_teacher_cannot_create_lesson_summary(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _single_session_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        "DENIED",
    )
    unrelated_class = _create_class(
        client,
        setup["admin_headers"],
        academy_id,
        branch_id,
        "OTHER",
    )
    _, other_headers = _identity(
        client,
        create_identity,
        academy_id,
        "workflow-other-teacher@example.com",
        (
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": branch_id,
                "scope_id": UUID(unrelated_class["id"]),
            },
        ),
    )

    denied = client.put(
        (
            f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
            "/lesson-summary"
        ),
        headers=other_headers,
        json=_summary_payload(academy_id),
    )

    assert denied.status_code == 403
    assert denied.json["error"]["code"] == "permission_denied"


def test_lesson_summary_edit_cannot_be_self_approved(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    setup = _single_session_setup(
        client,
        create_identity,
        academy_id,
        branch_id,
        "SELFAPPROVE",
    )
    path = (
        f"/api/v1/branches/{branch_id}/sessions/{setup['session_id']}"
        "/lesson-summary"
    )
    assert (
        client.put(
            path,
            headers=setup["teacher_headers"],
            json=_summary_payload(academy_id),
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{path}/publish",
            headers=setup["teacher_headers"],
            json={"academy_id": str(academy_id)},
        ).status_code
        == 200
    )
    summary = LessonSummary.query.one()
    requested = client.post(
        (
            f"/api/v1/branches/{branch_id}/lesson-summaries/{summary.id}"
            "/edit-requests"
        ),
        headers=setup["admin_headers"],
        json={
            **_summary_payload(academy_id, summary="Admin correction"),
            "reason": "Administrative wording correction",
        },
    )
    approval = client.post(
        (
            f"/api/v1/branches/{branch_id}/lesson-summary-edit-requests/"
            f"{requested.json['data']['id']}/approve"
        ),
        headers=setup["admin_headers"],
        json={"academy_id": str(academy_id), "reason": "Self reviewed"},
    )

    assert requested.status_code == 201
    assert approval.status_code == 403
    assert (
        approval.json["error"]["code"]
        == "lesson_summary_edit_self_approval_denied"
    )
