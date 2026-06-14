from uuid import uuid4

from app.extensions import db
from app.models.auth_session import AuthSession
from app.permissions.constants import Permission, Role, ScopeType
from app.permissions.context import AuthorizationTarget, Principal
from app.permissions.decorators import require_permission
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService


def test_multi_role_permissions_are_additive_but_scope_bound(
    app,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch_id = create_branch(
        academy_id=academy_id,
        name="Other Branch",
    ).id
    assigned_class_id = uuid4()
    user, assignments = create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "branch_id": other_branch_id,
                "scope_id": assigned_class_id,
            },
        ),
    )
    principal = Principal(
        user=user,
        session=AuthSession(user_id=user.id),
        assignments=tuple(assignments),
    )

    assert AuthorizationService.is_allowed(
        principal,
        Permission.SCHEDULE_CREATE,
        AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.SCHEDULE_CREATE,
        AuthorizationTarget(academy_id=academy_id, branch_id=other_branch_id),
    )
    assert AuthorizationService.is_allowed(
        principal,
        Permission.ATTENDANCE_CREATE,
        AuthorizationTarget(
            academy_id=academy_id,
            branch_id=other_branch_id,
            class_id=assigned_class_id,
        ),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.ATTENDANCE_CREATE,
        AuthorizationTarget(
            academy_id=academy_id,
            branch_id=other_branch_id,
            class_id=uuid4(),
        ),
    )


def test_academy_scope_never_crosses_tenant(
    create_identity,
    academy_id,
):
    user, assignments = create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    principal = Principal(
        user=user,
        session=AuthSession(user_id=user.id),
        assignments=tuple(assignments),
    )

    assert AuthorizationService.is_allowed(
        principal,
        Permission.REPORT_VIEW,
        AuthorizationTarget(academy_id=academy_id),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.REPORT_VIEW,
        AuthorizationTarget(academy_id=uuid4()),
    )


def test_platform_owner_does_not_receive_forbidden_operational_actions(
    identity,
):
    user = identity.create_user(
        academy_id=None,
        email="owner@platform.example",
        password="very-secure-password",
        full_name="Platform Owner",
    )
    assignment = identity.assign_role(
        user=user,
        role=Role.PLATFORM_OWNER,
        scope_type=ScopeType.PLATFORM,
    )
    principal = Principal(
        user=user,
        session=AuthSession(user_id=user.id),
        assignments=(assignment,),
    )

    assert AuthorizationService.is_allowed(
        principal,
        Permission.PLATFORM_MANAGE,
        AuthorizationTarget(),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.ATTENDANCE_CREATE,
        AuthorizationTarget(),
    )
    assert not AuthorizationService.is_allowed(
        principal,
        Permission.INVOICE_CREATE,
        AuthorizationTarget(),
    )


def test_revoked_role_stops_authorizing_existing_access_token(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, assignments = create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    login = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": user.email,
            "password": "very-secure-password",
        },
    ).json["data"]

    assignments[0].status = "revoked"
    db.session.commit()

    principal = AuthService().authenticate_access_token(login["access_token"])
    assert principal.assignments == ()


def test_permission_decorator_enforces_branch_scope_over_http(
    app,
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch_id = create_branch(
        academy_id=academy_id,
        name="Other Branch",
    ).id
    user, _ = create_identity(
        academy_id=academy_id,
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    def target_resolver(branch):
        return AuthorizationTarget(
            academy_id=academy_id,
            branch_id=branch,
        )

    @require_permission(Permission.SCHEDULE_CREATE, target_resolver)
    def protected_schedule(branch):
        return {"branch_id": str(branch)}

    app.add_url_rule(
        "/test/branches/<uuid:branch>/schedules",
        endpoint="test_create_schedule",
        view_func=protected_schedule,
    )
    access_token = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": user.email,
            "password": "very-secure-password",
        },
    ).json["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    allowed = client.get(
        f"/test/branches/{branch_id}/schedules",
        headers=headers,
    )
    denied = client.get(
        f"/test/branches/{other_branch_id}/schedules",
        headers=headers,
    )

    assert allowed.status_code == 200
    assert denied.status_code == 403
    assert denied.json["error"]["code"] == "permission_denied"
