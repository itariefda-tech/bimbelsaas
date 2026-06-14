from app.models.audit_log import AuditLog
from app.models.auth_session import AuthSession
from app.permissions.constants import Role, ScopeType


def _login(client, academy_id, password="very-secure-password"):
    return client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": "operator@example.com",
            "password": password,
        },
    )


def test_login_and_current_user_return_active_scoped_roles(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    login_response = _login(client, academy_id)

    assert login_response.status_code == 200
    tokens = login_response.json["data"]
    assert tokens["token_type"] == "Bearer"

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json["data"]["academy_id"] == str(academy_id)
    assert me_response.json["data"]["roles"] == [
        {
            "id": me_response.json["data"]["roles"][0]["id"],
            "role": "branch_admin",
            "scope_type": "branch",
            "academy_id": str(academy_id),
            "branch_id": str(branch_id),
            "scope_id": None,
        }
    ]
    assert AuthSession.query.count() == 1
    assert AuditLog.query.filter_by(action_type="auth.login").count() == 1


def test_login_is_academy_scoped(client, create_identity, academy_id, branch_id):
    create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    response = _login(client, "a4126b42-64ad-4ef4-b391-bf572c57bf2c")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "invalid_credentials"
    failed_audit = AuditLog.query.filter_by(
        action_type="auth.login_failed"
    ).one()
    assert failed_audit.new_data == {"success": False}


def test_refresh_rotates_token_and_replay_revokes_session(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    initial = _login(client, academy_id).json["data"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )

    assert refreshed.status_code == 200
    assert refreshed.json["data"]["refresh_token"] != initial["refresh_token"]

    replay = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )

    assert replay.status_code == 401
    assert replay.json["error"]["code"] == "refresh_token_reused"
    assert AuthSession.query.one().revoked_at is not None


def test_logout_revokes_access_session(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    access_token = _login(client, academy_id).json["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200

    denied = client.get("/api/v1/auth/me", headers=headers)
    assert denied.status_code == 401
    assert denied.json["error"]["code"] == "session_inactive"


def test_auth_endpoints_reject_missing_or_wrong_token_type(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    tokens = _login(client, academy_id).json["data"]

    missing = client.get("/api/v1/auth/me")
    wrong_type = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )

    assert missing.status_code == 401
    assert missing.json["error"]["code"] == "authentication_required"
    assert wrong_type.status_code == 401
    assert wrong_type.json["error"]["code"] == "invalid_token_type"
