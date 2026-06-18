from app.extensions import db
from app.models.student import Student
from app.permissions.constants import Role, ScopeType


def _login(client, email, academy_id=None):
    payload = {
        "email": email,
        "password": "very-secure-password",
    }
    if academy_id is not None:
        payload["academy_id"] = str(academy_id)
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['data']['access_token']}"}


def _platform_owner(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="scale-owner@example.com",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    return _login(client, user.email)


def _director(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="scale-director@example.com",
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
        email="scale-manager@example.com",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def test_scale_readiness_reports_cache_queue_and_ai_planning(
    client,
    create_identity,
):
    headers = _platform_owner(client, create_identity)

    response = client.get("/api/v1/scale/readiness", headers=headers)

    assert response.status_code == 200
    assert response.json["data"]["cache"]["enabled"] is True
    assert response.json["data"]["cache"]["backend"] == "in_memory"
    assert response.json["data"]["queues"]["status"] == "configured"
    assert response.json["data"]["ai_assistant_planning"]["status"] == "planned"


def test_non_platform_user_cannot_view_scale_readiness(
    client,
    create_identity,
    academy_id,
):
    headers = _director(client, create_identity, academy_id)

    response = client.get("/api/v1/scale/readiness", headers=headers)

    assert response.status_code == 403


def test_analytics_endpoint_reports_cache_hit_on_repeated_request(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _director(client, create_identity, academy_id)
    url = f"/api/v1/analytics/branches/{branch_id}/kpi"

    first = client.get(url, headers=headers)
    second = client.get(url, headers=headers)

    assert first.status_code == 200
    assert first.json["meta"]["cache"]["hit"] is False
    assert second.status_code == 200
    assert second.json["meta"]["cache"]["hit"] is True


def test_smart_scheduling_signals_are_branch_scoped_and_recommend_only(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    headers = _manager(client, create_identity, academy_id, branch_id)
    db.session.add(
        Student(
            academy_id=academy_id,
            home_branch_id=branch_id,
            student_code="SCALE-001",
            full_name="Scale Student",
            status="active",
        )
    )
    db.session.commit()

    response = client.get(
        f"/api/v1/scale/smart-scheduling/branches/{branch_id}/signals",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json["data"]["signals"]["active_students"] == 1
    assert response.json["data"]["mutation_policy"] == "recommendations_only"
    assert "assign_teachers_before_expanding_schedule" in response.json["data"]["recommendations"]
