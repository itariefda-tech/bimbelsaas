from app.extensions import db
from app.models.beta import BetaFeedback
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
        email="beta-owner@example.com",
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
        email="beta-director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    return _login(client, user.email, academy_id)


def _manager(client, create_identity, academy_id, branch_id, email):
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


def test_platform_owner_creates_and_activates_beta_onboarding(
    client,
    create_identity,
    academy_id,
):
    headers = _platform_owner(client, create_identity)

    created = client.post(
        "/api/v1/beta/onboardings",
        headers=headers,
        json={
            "academy_id": str(academy_id),
            "cohort_label": "Beta Cohort 1",
            "operational_owner_name": "Ops Lead",
            "operational_owner_contact": "ops@example.com",
            "success_criteria": {
                "minimum_live_classes": 10,
                "parent_feedback_sessions": 2,
            },
            "target_start_date": "2026-07-01",
            "target_end_date": "2026-07-31",
        },
    )
    activated = client.patch(
        f"/api/v1/beta/onboardings/{created.json['data']['id']}/status",
        headers=headers,
        json={"status": "active", "notes": "Kickoff complete."},
    )
    listed = client.get("/api/v1/beta/onboardings", headers=headers)
    readiness = client.get("/api/v1/beta/readiness", headers=headers)

    assert created.status_code == 201
    assert activated.status_code == 200
    assert activated.json["data"]["status"] == "active"
    assert listed.json["data"][0]["cohort_label"] == "Beta Cohort 1"
    assert readiness.json["data"]["active_onboardings"] == 1
    assert readiness.json["data"]["checklist"]["bug_feedback_intake"] is True


def test_academy_user_submits_feedback_and_director_triages_it(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    manager_headers = _manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "beta-manager@example.com",
    )
    director_headers = _director(client, create_identity, academy_id)

    submitted = client.post(
        "/api/v1/beta/feedback",
        headers=manager_headers,
        json={
            "academy_id": str(academy_id),
            "branch_id": str(branch_id),
            "category": "teacher_ux",
            "severity": "medium",
            "source_role": "teacher",
            "summary": "Timeline filter needs clearer default",
            "details": "Teachers expected today's branch sessions first.",
        },
    )
    feedback_id = submitted.json["data"]["id"]
    listed = client.get(
        f"/api/v1/beta/feedback?academy_id={academy_id}&branch_id={branch_id}",
        headers=director_headers,
    )
    triaged = client.patch(
        f"/api/v1/beta/feedback/{feedback_id}/status",
        headers=director_headers,
        json={"status": "triaged"},
    )

    assert submitted.status_code == 201
    assert listed.status_code == 200
    assert listed.json["data"][0]["summary"] == "Timeline filter needs clearer default"
    assert triaged.status_code == 200
    assert triaged.json["data"]["status"] == "triaged"


def test_branch_manager_cannot_list_other_branch_beta_feedback(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Beta Other")
    headers = _manager(
        client,
        create_identity,
        academy_id,
        branch_id,
        "beta-branch-manager@example.com",
    )

    response = client.get(
        f"/api/v1/beta/feedback?academy_id={academy_id}&branch_id={other_branch.id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_feedback_invalid_transition_is_rejected(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    director_headers = _director(client, create_identity, academy_id)
    feedback = BetaFeedback(
        academy_id=academy_id,
        branch_id=branch_id,
        reporter_user_id=None,
        category="bug",
        severity="high",
        source_role="admin",
        summary="Cannot complete beta flow",
        status="open",
    )
    db.session.add(feedback)
    db.session.commit()

    response = client.patch(
        f"/api/v1/beta/feedback/{feedback.id}/status",
        headers=director_headers,
        json={"status": "resolved"},
    )

    assert response.status_code == 409
