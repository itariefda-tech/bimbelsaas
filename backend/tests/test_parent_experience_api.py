from datetime import datetime, timezone
from app.extensions import db
from app.models.academic_class import AcademicClass
from app.models.attendance import Attendance
from app.models.class_session import ClassSession
from app.models.class_student import ClassStudent
from app.models.lesson_summary import LessonSummary
from app.models.room import Room
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.teacher import Teacher
from app.permissions.constants import Role, ScopeType
from app.services.identity_service import IdentityService


def _login(client, academy_id, email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": email,
            "password": "very-secure-password",
        },
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json['data']['access_token']}"
    }


def _setup_parent_data(
    client,
    identity,
    academy_id,
    branch_id,
):
    student = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="PARENT-001",
        full_name="Linked Child",
        status="active",
    )
    other_student = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="PARENT-002",
        full_name="Other Child",
        status="active",
    )
    academic_class = AcademicClass(
        academy_id=academy_id,
        branch_id=branch_id,
        class_code="PARENT-CLASS",
        class_name="English Intermediate",
        capacity=10,
        status="active",
    )
    teacher = Teacher(
        academy_id=academy_id,
        teacher_code="PARENT-TEACHER",
        full_name="Teacher Sarah",
        status="active",
        employment_status="active",
    )
    room = Room(
        academy_id=academy_id,
        branch_id=branch_id,
        room_code="PARENT-ROOM",
        room_name="Room 3A",
        capacity=10,
        status="available",
    )
    db.session.add_all(
        [student, other_student, academic_class, teacher, room]
    )
    db.session.flush()
    enrollment = ClassStudent(
        academy_id=academy_id,
        branch_id=branch_id,
        class_id=academic_class.id,
        student_id=student.id,
        enrollment_status="active",
    )
    first_schedule = Schedule(
        academy_id=academy_id,
        branch_id=branch_id,
        class_id=academic_class.id,
        teacher_id=teacher.id,
        room_id=room.id,
        starts_at=datetime(2026, 7, 5, 2, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 5, 4, 0, tzinfo=timezone.utc),
        timezone="Asia/Jakarta",
        status="completed",
    )
    second_schedule = Schedule(
        academy_id=academy_id,
        branch_id=branch_id,
        class_id=academic_class.id,
        teacher_id=teacher.id,
        room_id=room.id,
        starts_at=datetime(2026, 7, 12, 2, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 12, 4, 0, tzinfo=timezone.utc),
        timezone="Asia/Jakarta",
        status="cancelled",
    )
    db.session.add_all([enrollment, first_schedule, second_schedule])
    db.session.flush()
    first_session = ClassSession(
        academy_id=academy_id,
        branch_id=branch_id,
        schedule_id=first_schedule.id,
        status="completed",
        attendance_status="finalized",
        attendance_finalized_at=datetime(
            2026,
            7,
            5,
            4,
            5,
            tzinfo=timezone.utc,
        ),
    )
    second_session = ClassSession(
        academy_id=academy_id,
        branch_id=branch_id,
        schedule_id=second_schedule.id,
        status="cancelled",
        attendance_status="draft",
    )
    db.session.add_all([first_session, second_session])
    db.session.flush()
    actor_id = identity.create_user(
        academy_id=academy_id,
        email="parent-data-actor@example.com",
        password="very-secure-password",
        full_name="Data Actor",
    ).id
    db.session.add_all(
        [
            Attendance(
                academy_id=academy_id,
                branch_id=branch_id,
                session_id=first_session.id,
                schedule_id=first_schedule.id,
                class_id=academic_class.id,
                student_id=student.id,
                attendance_status="present",
                note="On time",
                recorded_by=actor_id,
                updated_by=actor_id,
            ),
            Attendance(
                academy_id=academy_id,
                branch_id=branch_id,
                session_id=second_session.id,
                schedule_id=second_schedule.id,
                class_id=academic_class.id,
                student_id=student.id,
                attendance_status="absent",
                recorded_by=actor_id,
                updated_by=actor_id,
            ),
            LessonSummary(
                academy_id=academy_id,
                branch_id=branch_id,
                session_id=first_session.id,
                schedule_id=first_schedule.id,
                class_id=academic_class.id,
                teacher_id=teacher.id,
                lesson_topic="Grammar Chapter 4",
                class_summary="Practiced present perfect tense.",
                teacher_notes="Strong participation.",
                homework="Exercise 1-5",
                student_attention_notes="Internal note",
                status="published",
                created_by=actor_id,
                updated_by=actor_id,
                published_by=actor_id,
                published_at=datetime(
                    2026,
                    7,
                    5,
                    4,
                    10,
                    tzinfo=timezone.utc,
                ),
            ),
            LessonSummary(
                academy_id=academy_id,
                branch_id=branch_id,
                session_id=second_session.id,
                schedule_id=second_schedule.id,
                class_id=academic_class.id,
                teacher_id=teacher.id,
                lesson_topic="Hidden Draft",
                class_summary="This must not be parent-visible.",
                status="draft",
                created_by=actor_id,
                updated_by=actor_id,
            ),
        ]
    )
    parent_user = identity.create_user(
        academy_id=academy_id,
        email="parent@example.com",
        password="very-secure-password",
        full_name="Linked Parent",
    )
    assignment = identity.assign_role(
        user=parent_user,
        role=Role.PARENT,
        scope_type=ScopeType.LINKED_STUDENT,
        academy_id=academy_id,
        branch_id=branch_id,
        scope_id=student.id,
        assigned_by=actor_id,
    )
    db.session.commit()
    return {
        "student": student,
        "other_student": other_student,
        "assignment": assignment,
        "headers": _login(client, academy_id, parent_user.email),
    }


def test_parent_dashboard_and_child_overview_are_link_scoped(
    client,
    identity,
    academy_id,
    branch_id,
):
    setup = _setup_parent_data(
        client,
        identity,
        academy_id,
        branch_id,
    )

    dashboard = client.get(
        "/api/v1/parent/dashboard",
        headers=setup["headers"],
    )
    overview = client.get(
        f"/api/v1/parent/children/{setup['student'].id}/overview",
        headers=setup["headers"],
    )
    denied = client.get(
        f"/api/v1/parent/children/{setup['other_student'].id}/overview",
        headers=setup["headers"],
    )

    assert dashboard.status_code == 200
    assert dashboard.json["data"]["linked_child_count"] == 1
    assert dashboard.json["data"]["children"][0]["full_name"] == "Linked Child"
    assert overview.status_code == 200
    assert overview.json["data"]["attendance"] == {
        "total_finalized_sessions": 1,
        "attended_sessions": 1,
        "percentage": 100.0,
        "by_status": {"present": 1},
    }
    assert overview.json["data"]["active_classes"][0]["name"] == (
        "English Intermediate"
    )
    assert overview.json["data"]["active_teachers"][0]["full_name"] == (
        "Teacher Sarah"
    )
    assert denied.status_code == 403


def test_parent_history_hides_drafts_and_schedule_keeps_changes_visible(
    client,
    identity,
    academy_id,
    branch_id,
):
    setup = _setup_parent_data(
        client,
        identity,
        academy_id,
        branch_id,
    )
    child_id = setup["student"].id
    headers = setup["headers"]

    attendance = client.get(
        f"/api/v1/parent/children/{child_id}/attendance",
        headers=headers,
    )
    summaries = client.get(
        f"/api/v1/parent/children/{child_id}/lesson-summaries",
        headers=headers,
    )
    schedule = client.get(
        (
            f"/api/v1/parent/children/{child_id}/schedule"
            "?from=2026-07-01T00:00:00Z&to=2026-07-20T00:00:00Z"
            "&timezone=Asia/Jakarta"
        ),
        headers=headers,
    )

    assert attendance.status_code == 200
    assert [item["attendance_status"] for item in attendance.json["data"]] == [
        "present"
    ]
    assert summaries.status_code == 200
    assert [item["lesson_topic"] for item in summaries.json["data"]] == [
        "Grammar Chapter 4"
    ]
    assert "student_attention_notes" not in summaries.json["data"][0]
    assert schedule.status_code == 200
    assert [item["status"] for item in schedule.json["data"]["items"]] == [
        "completed",
        "cancelled",
    ]
    assert schedule.json["data"]["items"][0]["starts_at"].endswith("+07:00")


def test_revoked_parent_link_stops_visibility(
    client,
    identity,
    academy_id,
    branch_id,
):
    setup = _setup_parent_data(
        client,
        identity,
        academy_id,
        branch_id,
    )

    identity.revoke_role(
        setup["assignment"],
        revoked_by=setup["assignment"].assigned_by,
    )
    db.session.commit()
    response = client.get(
        "/api/v1/parent/children",
        headers=setup["headers"],
    )

    assert response.status_code == 200
    assert response.json["data"] == []
