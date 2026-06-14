from uuid import uuid4

import pytest

from app.common.errors import ValidationError
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.auth_session import AuthSession
from app.models.role_assignment import RoleAssignment
from app.permissions.constants import Permission, Role, ScopeType
from app.permissions.context import AuthorizationTarget, Principal
from app.services.authorization_service import AuthorizationService


def _login(client, email, password, academy_id=None):
    payload = {"email": email, "password": password}
    if academy_id is not None:
        payload["academy_id"] = str(academy_id)
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json['data']['access_token']}"
    }


def _platform_owner(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="owner@platform.example",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    return _login(client, user.email, "very-secure-password")


def test_platform_owner_can_create_update_and_archive_academy(
    client,
    create_identity,
):
    headers = _platform_owner(client, create_identity)

    created = client.post(
        "/api/v1/academies",
        headers=headers,
        json={
            "name": "Premium Academy",
            "slug": "premium-academy",
            "timezone": "Asia/Jakarta",
            "currency": "idr",
        },
    )
    assert created.status_code == 201
    academy_id = created.json["data"]["id"]

    updated = client.patch(
        f"/api/v1/academies/{academy_id}",
        headers=headers,
        json={"name": "Premium Academy Indonesia", "status": "suspended"},
    )
    assert updated.status_code == 200
    assert updated.json["data"]["status"] == "suspended"

    archived = client.delete(
        f"/api/v1/academies/{academy_id}",
        headers=headers,
    )
    assert archived.status_code == 200
    assert archived.json["data"]["status"] == "archived"
    assert archived.json["data"]["archived_at"] is not None
    assert AuditLog.query.filter_by(action_type="academy.archived").count() == 1


def test_academy_director_can_manage_own_branches(
    client,
    create_identity,
    academy_id,
):
    director, _ = create_identity(
        academy_id=academy_id,
        email="director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    headers = _login(
        client,
        director.email,
        "very-secure-password",
        academy_id,
    )

    created = client.post(
        f"/api/v1/academies/{academy_id}/branches",
        headers=headers,
        json={
            "name": "Meruya",
            "code": "mry",
            "timezone": "Asia/Jakarta",
            "address": "Jakarta",
        },
    )

    assert created.status_code == 201
    assert created.json["data"]["code"] == "MRY"
    branch_id = created.json["data"]["id"]

    updated = client.patch(
        f"/api/v1/branches/{branch_id}",
        headers=headers,
        json={"status": "maintenance"},
    )
    assert updated.status_code == 200
    assert updated.json["data"]["status"] == "maintenance"

    listed = client.get(
        f"/api/v1/academies/{academy_id}/branches",
        headers=headers,
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json["data"]] == [branch_id]


def test_branch_manager_cannot_see_or_modify_another_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
):
    assigned_branch = create_branch(
        academy_id=academy_id,
        name="Assigned Branch",
        code="ASSIGNED",
    )
    other_branch = create_branch(
        academy_id=academy_id,
        name="Other Branch",
        code="OTHER",
    )
    manager, _ = create_identity(
        academy_id=academy_id,
        email="manager@example.com",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": assigned_branch.id,
            },
        ),
    )
    headers = _login(
        client,
        manager.email,
        "very-secure-password",
        academy_id,
    )

    listed = client.get(
        f"/api/v1/academies/{academy_id}/branches",
        headers=headers,
    )
    denied_view = client.get(
        f"/api/v1/branches/{other_branch.id}",
        headers=headers,
    )
    denied_edit = client.patch(
        f"/api/v1/branches/{other_branch.id}",
        headers=headers,
        json={"name": "Unauthorized Rename"},
    )
    allowed_edit = client.patch(
        f"/api/v1/branches/{assigned_branch.id}",
        headers=headers,
        json={"name": "Assigned Branch Updated"},
    )

    assert [item["id"] for item in listed.json["data"]] == [
        str(assigned_branch.id)
    ]
    assert denied_view.status_code == 403
    assert denied_edit.status_code == 403
    assert allowed_edit.status_code == 200


def test_branch_admin_cannot_edit_branch_profile(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    admin, _ = create_identity(
        academy_id=academy_id,
        email="admin@example.com",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    headers = _login(
        client,
        admin.email,
        "very-secure-password",
        academy_id,
    )

    response = client.patch(
        f"/api/v1/branches/{branch_id}",
        headers=headers,
        json={"name": "Forbidden Rename"},
    )

    assert response.status_code == 403


def test_non_operational_branch_blocks_operational_permissions(
    create_identity,
    create_branch,
    academy_id,
):
    branch = create_branch(
        academy_id=academy_id,
        status="maintenance",
    )
    user, _ = create_identity(
        academy_id=academy_id,
        assignments=(),
    )

    scoped_assignment = RoleAssignment(
        user_id=user.id,
        role=Role.BRANCH_MANAGER,
        scope_type=ScopeType.BRANCH,
        scope_key=f"branch:{branch.id}",
        academy_id=academy_id,
        branch_id=branch.id,
    )
    db.session.add(scoped_assignment)
    db.session.flush()
    principal = Principal(
        user=user,
        session=AuthSession(user_id=user.id),
        assignments=(scoped_assignment,),
    )

    assert AuthorizationService.is_allowed(
        principal,
        Permission.BRANCH_VIEW,
        AuthorizationTarget(academy_id=academy_id, branch_id=branch.id),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.SCHEDULE_CREATE,
        AuthorizationTarget(academy_id=academy_id, branch_id=branch.id),
    )


def test_cross_academy_branch_assignment_is_rejected(
    identity,
    create_academy,
    create_branch,
    academy_id,
):
    other_academy = create_academy(
        name="Other Academy",
        slug=f"other-{uuid4().hex[:8]}",
    )
    other_branch = create_branch(academy_id=other_academy.id)
    user = identity.create_user(
        academy_id=academy_id,
        email="user@example.com",
        password="very-secure-password",
        full_name="User Name",
    )

    with pytest.raises(ValidationError, match="belong to the academy"):
        identity.assign_role(
            user=user,
            role=Role.BRANCH_ADMIN,
            scope_type=ScopeType.BRANCH,
            academy_id=academy_id,
            branch_id=other_branch.id,
        )


def test_academy_director_cannot_cross_tenant(
    client,
    create_identity,
    create_academy,
    academy_id,
):
    other_academy = create_academy(name="Other Academy")
    director, _ = create_identity(
        academy_id=academy_id,
        email="director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    headers = _login(
        client,
        director.email,
        "very-secure-password",
        academy_id,
    )

    response = client.get(
        f"/api/v1/academies/{other_academy.id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_suspended_academy_is_read_only_for_director(
    client,
    create_identity,
    academy,
):
    director, _ = create_identity(
        academy_id=academy.id,
        email="director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    headers = _login(
        client,
        director.email,
        "very-secure-password",
        academy.id,
    )
    academy.status = "suspended"
    db.session.commit()

    readable = client.get(
        f"/api/v1/academies/{academy.id}",
        headers=headers,
    )
    blocked = client.post(
        f"/api/v1/academies/{academy.id}/branches",
        headers=headers,
        json={"name": "Blocked Branch", "code": "BLOCKED"},
    )

    assert readable.status_code == 200
    assert blocked.status_code == 409
    assert blocked.json["error"]["code"] == "academy_not_operational"


def test_archived_branch_is_terminal_and_excluded_from_operational_list(
    client,
    create_identity,
    create_branch,
    academy_id,
):
    branch = create_branch(academy_id=academy_id, name="Archive Me")
    director, _ = create_identity(
        academy_id=academy_id,
        email="director@example.com",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    headers = _login(
        client,
        director.email,
        "very-secure-password",
        academy_id,
    )

    archived = client.delete(
        f"/api/v1/branches/{branch.id}",
        headers=headers,
    )
    edit_archived = client.patch(
        f"/api/v1/branches/{branch.id}",
        headers=headers,
        json={"status": "active"},
    )
    listed = client.get(
        f"/api/v1/academies/{academy_id}/branches",
        headers=headers,
    )

    assert archived.status_code == 200
    assert archived.json["data"]["status"] == "archived"
    assert edit_archived.status_code == 409
    assert listed.json["data"] == []
