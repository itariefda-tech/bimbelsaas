from uuid import UUID, uuid4

from app.models.audit_log import AuditLog
from app.permissions.constants import Role, ScopeType
from app.services.cross_branch_policy import CrossBranchPolicy
from app.services.student_service import StudentService


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
    return {
        "Authorization": f"Bearer {response.json['data']['access_token']}"
    }


def _director(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _branch_manager(client, create_identity, academy_id, branch_id, email):
    user, _ = create_identity(
        academy_id=academy_id,
        email=email,
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def test_teacher_can_be_explicitly_assigned_to_multiple_branches(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    second_branch = create_branch(academy_id=academy_id, name="Second Branch")
    headers = _director(client, create_identity, academy_id)

    created = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-001",
            "full_name": "Teacher One",
            "specialization": "English",
        },
    )
    teacher_id = created.json["data"]["id"]
    assigned = client.post(
        f"/api/v1/academies/{academy_id}/teachers/{teacher_id}/branches/{second_branch.id}",
        headers=headers,
    )
    loaded = client.get(
        f"/api/v1/academies/{academy_id}/teachers/{teacher_id}",
        headers=headers,
    )

    assert created.status_code == 201
    assert assigned.status_code == 201
    assert loaded.json["data"]["branch_ids"] == sorted(
        [str(branch_id), str(second_branch.id)]
    )
    policy = CrossBranchPolicy()
    assert policy.teacher_is_assigned(
        UUID(teacher_id),
        second_branch.id,
    )
    assert AuditLog.query.filter_by(
        action_type="teacher.branch_assigned"
    ).count() == 1


def test_branch_manager_cannot_assign_teacher_to_another_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    second_branch = create_branch(academy_id=academy_id, name="Other Branch")
    director_headers = _director(client, create_identity, academy_id)
    created = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-002",
            "full_name": "Teacher Two",
        },
    )
    manager_headers = _branch_manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "manager@example.com",
    )

    response = client.post(
        f"/api/v1/academies/{academy_id}/teachers/{created.json['data']['id']}/branches/{second_branch.id}",
        headers=manager_headers,
    )

    assert response.status_code == 403


def test_teacher_must_keep_one_active_branch(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    created = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-003",
            "full_name": "Teacher Three",
        },
    )

    response = client.delete(
        f"/api/v1/academies/{academy_id}/teachers/{created.json['data']['id']}/branches/{branch_id}",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json["error"]["code"] == "teacher_requires_branch"


def test_teacher_branch_assignment_can_end_when_another_branch_remains(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Branch")
    headers = _director(client, create_identity, academy_id)
    teacher = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-004",
            "full_name": "Teacher Four",
        },
    ).json["data"]
    client.post(
        f"/api/v1/academies/{academy_id}/teachers/{teacher['id']}/branches/{other_branch.id}",
        headers=headers,
    )

    removed = client.delete(
        f"/api/v1/academies/{academy_id}/teachers/{teacher['id']}/branches/{branch_id}",
        headers=headers,
    )

    assert removed.status_code == 200
    assert removed.json["data"]["assignment_status"] == "ended"


def test_archiving_teacher_ends_active_branch_assignments(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    teacher = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-005",
            "full_name": "Teacher Five",
        },
    ).json["data"]

    archived = client.delete(
        f"/api/v1/academies/{academy_id}/teachers/{teacher['id']}",
        headers=headers,
    )

    assert archived.status_code == 200
    assert archived.json["data"]["status"] == "archived"
    assert archived.json["data"]["branch_ids"] == []


def test_teacher_and_student_lists_are_branch_isolated(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Branch")
    director_headers = _director(client, create_identity, academy_id)
    teacher_one = client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-A",
            "full_name": "Teacher A",
        },
    ).json["data"]
    client.post(
        f"/api/v1/branches/{other_branch.id}/teachers",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-B",
            "full_name": "Teacher B",
        },
    )
    student_one = client.post(
        f"/api/v1/branches/{branch_id}/students",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-A",
            "full_name": "Student A",
        },
    ).json["data"]
    client.post(
        f"/api/v1/branches/{other_branch.id}/students",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-B",
            "full_name": "Student B",
        },
    )
    manager_headers = _branch_manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "manager@example.com",
    )

    teachers = client.get(
        f"/api/v1/academies/{academy_id}/teachers",
        headers=manager_headers,
    )
    students = client.get(
        f"/api/v1/academies/{academy_id}/students",
        headers=manager_headers,
    )

    assert [item["id"] for item in teachers.json["data"]] == [teacher_one["id"]]
    assert [item["id"] for item in students.json["data"]] == [student_one["id"]]


def test_student_home_branch_is_mandatory_and_cross_branch_defaults_to_deny(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Branch")
    headers = _director(client, create_identity, academy_id)
    created = client.post(
        f"/api/v1/branches/{branch_id}/students",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-001",
            "full_name": "Student One",
            "birth_date": "2015-04-03",
        },
    )
    student_id = created.json["data"]["id"]

    home_access = client.get(
        f"/api/v1/academies/{academy_id}/students/{student_id}/branch-access/{branch_id}",
        headers=headers,
    )
    other_access = client.get(
        f"/api/v1/academies/{academy_id}/students/{student_id}/branch-access/{other_branch.id}",
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json["data"]["home_branch_id"] == str(branch_id)
    assert home_access.json["data"] == {
        "student_id": student_id,
        "branch_id": str(branch_id),
        "allowed": True,
        "source": "home_branch",
    }
    assert other_access.json["data"]["allowed"] is False
    assert other_access.json["data"]["source"] == "default_deny"


def test_branch_manager_cannot_move_student_to_unmanaged_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Branch")
    director_headers = _director(client, create_identity, academy_id)
    student = client.post(
        f"/api/v1/branches/{branch_id}/students",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-002",
            "full_name": "Student Two",
        },
    ).json["data"]
    manager_headers = _branch_manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "manager@example.com",
    )

    response = client.patch(
        f"/api/v1/academies/{academy_id}/students/{student['id']}",
        headers=manager_headers,
        json={"home_branch_id": str(other_branch.id)},
    )

    assert response.status_code == 403


def test_cross_branch_policy_has_future_entitlement_hook(
    create_identity,
    academy_id,
    branch_id,
    create_branch,
):
    other_branch = create_branch(academy_id=academy_id, name="Premium Branch")
    director_user, assignments = create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    from app.models.auth_session import AuthSession
    from app.permissions.context import Principal

    principal = Principal(
        user=director_user,
        session=AuthSession(user_id=director_user.id),
        assignments=tuple(assignments),
    )
    student = StudentService().create(
        principal,
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="S-003",
        full_name="Student Three",
    )
    policy = CrossBranchPolicy(
        student_entitlement_provider=lambda student_id, target_branch_id: (
            student_id == student.id and target_branch_id == other_branch.id
        )
    )

    assert policy.student_can_access(student, other_branch.id)


def test_branch_summary_counts_only_scoped_active_profiles(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Other Branch")
    director_headers = _director(client, create_identity, academy_id)
    client.post(
        f"/api/v1/branches/{branch_id}/teachers",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "teacher_code": "T-SUM",
            "full_name": "Summary Teacher",
        },
    )
    client.post(
        f"/api/v1/branches/{branch_id}/students",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-SUM",
            "full_name": "Summary Student",
        },
    )
    client.post(
        f"/api/v1/branches/{other_branch.id}/students",
        headers=director_headers,
        json={
            "academy_id": str(academy_id),
            "student_code": "S-OTHER",
            "full_name": "Other Student",
        },
    )
    manager_headers = _branch_manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "summary-manager@example.com",
    )

    summary = client.get(
        f"/api/v1/branches/{branch_id}/summary",
        headers=manager_headers,
    )
    denied = client.get(
        f"/api/v1/branches/{other_branch.id}/summary",
        headers=manager_headers,
    )

    assert summary.status_code == 200
    assert summary.json["data"]["active_students"] == 1
    assert summary.json["data"]["active_teachers"] == 1
    assert denied.status_code == 403
