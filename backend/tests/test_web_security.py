from uuid import uuid4

from app import create_app
from app.config import ProductionConfig
from app.extensions import db
from app.models.academy import Academy
from app.models.branch import Branch
from app.models.role_assignment import RoleAssignment
from app.models.student import Student
from app.permissions.constants import Role, ScopeType
from tests.conftest import TestConfig


def _csrf_from_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    return _csrf_from_body(response.get_data(as_text=True))


def _csrf_from_body(body):
    marker = 'name="_csrf_token" value="'
    start = body.index(marker) + len(marker)
    end = body.index('"', start)
    return body[start:end]


def test_login_rejects_missing_csrf_token(client):
    response = client.post(
        "/login",
        data={"email": "owner@example.com", "password": "password123"},
    )

    assert response.status_code == 400


def test_login_page_shows_frontend_foundation(client):
    response = client.get("/login")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Secure operations shell" in body
    assert "Role-aware" in body
    assert "CSRF protected" in body


def test_login_accepts_valid_csrf_token(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="web-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    response = client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_dashboard_shows_role_specific_polish(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="polish-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get("/dashboard/platform_owner")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Global SaaS command center" in body
    assert "Role focus" in body
    assert "Quick actions" in body
    assert "Review staging runbook" in body


def test_platform_owner_can_register_tenant_from_web(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="tenant-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get("/tenants")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Tenant Registration" in body
    assert "Create tenant" in body

    response = client.post(
        "/tenants",
        data={
            "name": "Connected Academy",
            "slug": "connected-academy",
            "timezone": "Asia/Jakarta",
            "currency": "idr",
            "logo_url": "",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Tenant Connected Academy berhasil dibuat." in body
    assert "Connected Academy" in body
    assert "connected-academy / Asia/Jakarta / IDR" in body


def test_tenant_registration_shows_duplicate_slug_error(client, create_identity):
    user, _ = create_identity(
        academy_id=None,
        email="tenant-duplicate-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get("/tenants")
    token = _csrf_from_body(page.get_data(as_text=True))
    payload = {
        "name": "Duplicate Academy",
        "slug": "duplicate-academy",
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "logo_url": "",
        "_csrf_token": token,
    }
    first = client.post("/tenants", data=payload)
    assert first.status_code == 302

    page = client.get("/tenants")
    payload["_csrf_token"] = _csrf_from_body(page.get_data(as_text=True))
    second = client.post("/tenants", data=payload)
    body = second.get_data(as_text=True)

    assert second.status_code == 409
    assert "An academy with this slug already exists." in body
    assert 'value="duplicate-academy"' in body


def test_tenant_registration_is_platform_owner_only(
    client,
    create_identity,
    academy_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="tenant-director@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )

    response = client.get("/tenants")
    body = response.get_data(as_text=True)

    assert response.status_code == 403
    assert "Error 403" in body


def test_platform_owner_can_update_academy_setup_and_create_branch(
    client,
    create_identity,
):
    user, _ = create_identity(
        academy_id=None,
        email="setup-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    tenants = client.get("/tenants")
    created = client.post(
        "/tenants",
        data={
            "name": "Setup Academy",
            "slug": "setup-academy",
            "timezone": "Asia/Jakarta",
            "currency": "IDR",
            "logo_url": "",
            "_csrf_token": _csrf_from_body(tenants.get_data(as_text=True)),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)
    marker = "/academies/"
    start = body.index(marker) + len(marker)
    end = body.index("/setup", start)
    academy_id = body[start:end]

    setup = client.get(f"/academies/{academy_id}/setup")
    body = setup.get_data(as_text=True)

    assert setup.status_code == 200
    assert "Initial academy setup" in body
    assert "No branch created yet" in body

    updated = client.post(
        f"/academies/{academy_id}/setup",
        data={
            "name": "Setup Academy Updated",
            "slug": "setup-academy-updated",
            "timezone": "Asia/Jakarta",
            "currency": "idr",
            "logo_url": "https://example.com/logo.png",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = updated.get_data(as_text=True)

    assert updated.status_code == 200
    assert "Academy Setup Academy Updated berhasil diperbarui." in body
    assert "Setup Academy Updated" in body
    assert 'value="setup-academy-updated"' in body

    branched = client.post(
        f"/academies/{academy_id}/branches",
        data={
            "name": "Meruya Branch",
            "code": "mry",
            "timezone": "Asia/Jakarta",
            "address": "Jakarta Barat",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = branched.get_data(as_text=True)

    assert branched.status_code == 200
    assert "Branch Meruya Branch berhasil dibuat." in body
    assert "MRY / Asia/Jakarta / Jakarta Barat" in body

    marker = f"/academies/{academy_id}/branches/"
    start = body.index(marker) + len(marker)
    end = body.index('"', start)
    branch_id = body[start:end]

    edited = client.post(
        f"/academies/{academy_id}/branches/{branch_id}",
        data={
            "name": "Meruya Branch Updated",
            "code": "mry-2",
            "timezone": "Asia/Jakarta",
            "address": "Jakarta Barat Updated",
            "status": "maintenance",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = edited.get_data(as_text=True)

    assert edited.status_code == 200
    assert "Branch Meruya Branch Updated berhasil diperbarui." in body
    assert "MRY-2 / Asia/Jakarta / Jakarta Barat Updated" in body
    assert "maintenance" in body

    archived = client.post(
        f"/academies/{academy_id}/branches/{branch_id}/archive",
        data={"_csrf_token": _csrf_from_body(body)},
        follow_redirects=True,
    )
    body = archived.get_data(as_text=True)

    assert archived.status_code == 200
    assert "Branch Meruya Branch Updated berhasil diarsipkan." in body
    assert "No branch created yet" in body


def test_academy_director_can_open_own_academy_setup(
    client,
    create_identity,
    academy_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="setup-director@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get(f"/academies/{academy_id}/setup")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Initial academy setup" in body
    assert "Create first branch" in body


def test_suspended_academy_setup_is_read_only_for_director(
    client,
    create_identity,
    academy_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="setup-suspended-director@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    academy = db.session.get(Academy, academy_id)
    academy.status = "suspended"
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get(f"/academies/{academy_id}/setup")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Suspended" in body
    assert "Profile editing is currently read-only" in body
    assert "Branch creation is locked" in body


def test_branch_admin_cannot_create_branch_from_setup(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="setup-branch-admin@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    setup = client.get(f"/academies/{academy_id}/setup")
    body = setup.get_data(as_text=True)

    assert setup.status_code == 200
    denied = client.post(
        f"/academies/{academy_id}/branches",
        data={
            "name": "Denied Branch",
            "code": "DENIED",
            "timezone": "Asia/Jakarta",
            "address": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


def test_branch_admin_cannot_edit_branch_profile_from_setup(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    branch = db.session.get(Branch, branch_id)
    user, _ = create_identity(
        academy_id=academy_id,
        email="setup-branch-admin-edit@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    setup = client.get(f"/academies/{academy_id}/setup")
    body = setup.get_data(as_text=True)

    assert setup.status_code == 200
    assert "Branch creation is locked" in body
    assert "Save branch" not in body

    denied = client.post(
        f"/academies/{academy_id}/branches/{branch.id}",
        data={
            "name": "Denied Branch Edit",
            "code": branch.code,
            "timezone": branch.timezone,
            "address": "",
            "status": branch.status,
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


def test_platform_owner_can_create_assign_and_revoke_internal_role(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=None,
        email="team-owner@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PLATFORM_OWNER,
                "scope_type": ScopeType.PLATFORM,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/team")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Internal role setup" in body
    assert "Create and assign role" in body

    created = client.post(
        f"/academies/{academy_id}/team/users",
        data={
            "full_name": "Internal Director",
            "email": "internal-director@example.com",
            "password": "password12345",
            "role": Role.ACADEMY_DIRECTOR.value,
            "branch_id": "",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)

    assert created.status_code == 200
    assert "Internal user Internal Director berhasil dibuat dan diberi role." in body
    assert "internal-director@example.com" in body
    assert "Academy Director" in body

    created_user = db.session.scalar(
        db.select(RoleAssignment).where(
            RoleAssignment.role == Role.ACADEMY_DIRECTOR.value,
            RoleAssignment.academy_id == academy_id,
        )
    ).user

    assigned = client.post(
        f"/academies/{academy_id}/team/assignments",
        data={
            "user_id": str(created_user.id),
            "role": Role.BRANCH_MANAGER.value,
            "branch_id": str(branch_id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = assigned.get_data(as_text=True)

    assert assigned.status_code == 200
    assert "Internal role berhasil ditambahkan." in body
    assert "Branch Manager" in body

    assignment = db.session.scalar(
        db.select(RoleAssignment).where(
            RoleAssignment.user_id == created_user.id,
            RoleAssignment.role == Role.BRANCH_MANAGER.value,
            RoleAssignment.branch_id == branch_id,
            RoleAssignment.status == "active",
        )
    )
    revoked = client.post(
        f"/academies/{academy_id}/team/assignments/{assignment.id}/revoke",
        data={"_csrf_token": _csrf_from_body(body)},
        follow_redirects=True,
    )
    body = revoked.get_data(as_text=True)

    assert revoked.status_code == 200
    assert "Internal role berhasil dicabut." in body
    assert db.session.get(RoleAssignment, assignment.id).status == "revoked"


def test_academy_director_can_create_branch_admin_for_own_branch(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="team-director@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/team")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Internal role setup" in body
    assert "Tenant list" not in body

    created = client.post(
        f"/academies/{academy_id}/team/users",
        data={
            "full_name": "Branch Admin New",
            "email": "branch-admin-new@example.com",
            "password": "password12345",
            "role": Role.BRANCH_ADMIN.value,
            "branch_id": str(branch_id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)

    assert created.status_code == 200
    assert "Branch Admin New" in body
    assert "Branch Admin" in body


def test_internal_role_setup_rejects_invalid_scope(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="team-invalid-director@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.ACADEMY_DIRECTOR,
                "scope_type": ScopeType.ACADEMY,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/team")
    body = page.get_data(as_text=True)

    response = client.post(
        f"/academies/{academy_id}/team/users",
        data={
            "full_name": "Invalid Director Scope",
            "email": "invalid-director-scope@example.com",
            "password": "password12345",
            "role": Role.ACADEMY_DIRECTOR.value,
            "branch_id": str(branch_id),
            "_csrf_token": _csrf_from_body(body),
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 422
    assert "Academy scope cannot include branch or entity IDs." in body
    assert 'value="invalid-director-scope@example.com"' in body


def test_branch_admin_cannot_manage_internal_roles(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="team-branch-admin@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/team")

    assert page.status_code == 403


def test_teacher_dashboard_shows_daily_workflow(client, create_identity, academy_id):
    user, _ = create_identity(
        academy_id=academy_id,
        email="polish-teacher@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.TEACHER,
                "scope_type": ScopeType.ASSIGNED_CLASS,
                "scope_id": uuid4(),
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get("/dashboard/teacher")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Teacher Dashboard" in body
    assert "Today teaching flow" in body
    assert "Next class" in body
    assert "Lesson summary" in body


def test_parent_dashboard_shows_monitoring_workflow(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    student = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="WEB-PARENT-001",
        full_name="Linked Web Child",
        status="active",
    )
    db.session.add(student)
    db.session.flush()

    user, _ = create_identity(
        academy_id=academy_id,
        email="polish-parent@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.PARENT,
                "scope_type": ScopeType.LINKED_STUDENT,
                "scope_id": student.id,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get("/dashboard/parent")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Parent Dashboard" in body
    assert "Monitoring flow" in body
    assert "Activity feed" in body
    assert "Parent trust states" in body
    assert "Only linked students are visible" in body


def test_branch_admin_dashboard_shows_operational_workflow(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="polish-admin@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )
    db.session.commit()

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    response = client.get("/dashboard/branch_admin")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Branch Admin Dashboard" in body
    assert "Branch admin operations flow" in body
    assert "Find the student, parent, class, or invoice first" in body
    assert "Branch admin operational states" in body
    assert "Outside branch scope" in body


def test_session_cookie_security_defaults():
    app = create_app(TestConfig)

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_production_rejects_demo_login_hints():
    class UnsafeProductionConfig(ProductionConfig):
        SECRET_KEY = "x" * 32
        SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://user:pass@db/app"
        REDIS_URL = "redis://cache:6379/0"
        RATE_LIMIT_ENABLED = True
        DEMO_LOGIN_HINTS_ENABLED = True
        DEMO_SEED_ENABLED = False

    try:
        UnsafeProductionConfig.validate()
    except RuntimeError as error:
        assert "DEMO_LOGIN_HINTS_ENABLED" in str(error)
    else:
        raise AssertionError("Expected production demo hints to be rejected.")
