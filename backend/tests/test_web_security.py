from datetime import datetime
from uuid import uuid4

from app import create_app
from app.config import ProductionConfig
from app.extensions import db
from app.models.academy import Academy
from app.models.academic_class import AcademicClass
from app.models.branch import Branch
from app.models.class_student import ClassStudent
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.role_assignment import RoleAssignment
from app.models.room import Room
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_branch import TeacherBranch
from app.models.user import User
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


def _seed_schedule_ready_context(identity, academy_id, branch_id, *, suffix="001"):
    teacher_user = identity.create_user(
        academy_id=academy_id,
        email=f"cw9-teacher-{suffix}@example.com",
        password="password12345",
        full_name=f"CW9 Teacher {suffix}",
    )
    student_user = identity.create_user(
        academy_id=academy_id,
        email=f"cw9-student-{suffix}@example.com",
        password="password12345",
        full_name=f"CW9 Student {suffix}",
    )
    parent_user = identity.create_user(
        academy_id=academy_id,
        email=f"cw9-parent-{suffix}@example.com",
        password="password12345",
        full_name=f"CW9 Parent {suffix}",
    )
    academic_class = AcademicClass(
        academy_id=academy_id,
        branch_id=branch_id,
        class_code=f"CW9-C-{suffix}".upper(),
        class_name=f"CW9 Class {suffix}",
        capacity=12,
        status="active",
    )
    room = Room(
        academy_id=academy_id,
        branch_id=branch_id,
        room_code=f"CW9-R-{suffix}".upper(),
        room_name=f"CW9 Room {suffix}",
        capacity=16,
        status="available",
    )
    teacher = Teacher(
        academy_id=academy_id,
        user_id=teacher_user.id,
        teacher_code=f"CW9-T-{suffix}".upper(),
        full_name=f"CW9 Teacher {suffix}",
        status="active",
        employment_status="active",
    )
    student = Student(
        academy_id=academy_id,
        user_id=student_user.id,
        student_code=f"CW9-S-{suffix}".upper(),
        full_name=f"CW9 Student {suffix}",
        home_branch_id=branch_id,
        status="active",
    )
    db.session.add_all([academic_class, room, teacher, student])
    db.session.flush()
    db.session.add(
        TeacherBranch(
            academy_id=academy_id,
            branch_id=branch_id,
            teacher_id=teacher.id,
            assignment_status="active",
        )
    )
    db.session.add(
        ClassStudent(
            academy_id=academy_id,
            branch_id=branch_id,
            class_id=academic_class.id,
            student_id=student.id,
            enrollment_status="active",
        )
    )
    db.session.flush()
    identity.assign_role(
        user=teacher_user,
        role=Role.TEACHER,
        scope_type=ScopeType.ASSIGNED_CLASS,
        academy_id=academy_id,
        branch_id=branch_id,
        scope_id=academic_class.id,
    )
    identity.assign_role(
        user=student_user,
        role=Role.STUDENT,
        scope_type=ScopeType.SELF,
        academy_id=academy_id,
    )
    identity.assign_role(
        user=parent_user,
        role=Role.PARENT,
        scope_type=ScopeType.LINKED_STUDENT,
        academy_id=academy_id,
        branch_id=branch_id,
        scope_id=student.id,
    )
    db.session.commit()
    return {
        "teacher_user": teacher_user,
        "student_user": student_user,
        "parent_user": parent_user,
        "teacher": teacher,
        "student": student,
        "academic_class": academic_class,
        "room": room,
    }


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


def test_academy_director_can_create_teacher_user_profile_and_branch_assignment(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="teacher-flow-director@example.com",
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
    page = client.get(f"/academies/{academy_id}/teachers")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Teacher registration" in body
    assert "Create teacher" in body

    created = client.post(
        f"/academies/{academy_id}/teachers",
        data={
            "teacher_code": "web-t-001",
            "full_name": "Web Teacher One",
            "employment_status": "active",
            "specialization": "English",
            "branch_id": str(branch_id),
            "user_id": "",
            "user_email": "web-teacher-one@example.com",
            "user_password": "password12345",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)

    assert created.status_code == 200
    assert "Teacher Web Teacher One berhasil dibuat dan dihubungkan ke branch." in body
    assert "WEB-T-001" in body
    assert "web-teacher-one@example.com" in body

    teacher = db.session.scalar(
        db.select(Teacher).where(
            Teacher.academy_id == academy_id,
            Teacher.teacher_code == "WEB-T-001",
        )
    )
    teacher_user = db.session.get(User, teacher.user_id)
    assignment = db.session.scalar(
        db.select(TeacherBranch).where(
            TeacherBranch.teacher_id == teacher.id,
            TeacherBranch.branch_id == branch_id,
        )
    )

    assert teacher.full_name == "Web Teacher One"
    assert teacher_user.email == "web-teacher-one@example.com"
    assert assignment.assignment_status == "active"


def test_teacher_branch_assignment_can_be_ended_from_web_when_another_branch_remains(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Teacher Other Branch")
    user, _ = create_identity(
        academy_id=academy_id,
        email="teacher-assign-director@example.com",
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
    page = client.get(f"/academies/{academy_id}/teachers")
    created = client.post(
        f"/academies/{academy_id}/teachers",
        data={
            "teacher_code": "WEB-T-002",
            "full_name": "Web Teacher Two",
            "employment_status": "active",
            "specialization": "Math",
            "branch_id": str(branch_id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(page.get_data(as_text=True)),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)
    teacher = db.session.scalar(
        db.select(Teacher).where(Teacher.teacher_code == "WEB-T-002")
    )

    assigned = client.post(
        f"/academies/{academy_id}/teachers/{teacher.id}/branches",
        data={
            "branch_id": str(other_branch.id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = assigned.get_data(as_text=True)

    assert assigned.status_code == 200
    assert "Teacher branch assignment berhasil diaktifkan." in body

    ended = client.post(
        f"/academies/{academy_id}/teachers/{teacher.id}/branches/{branch_id}/end",
        data={"_csrf_token": _csrf_from_body(body)},
        follow_redirects=True,
    )
    body = ended.get_data(as_text=True)
    ended_assignment = db.session.scalar(
        db.select(TeacherBranch).where(
            TeacherBranch.teacher_id == teacher.id,
            TeacherBranch.branch_id == branch_id,
        )
    )

    assert ended.status_code == 200
    assert "Teacher branch assignment berhasil diakhiri." in body
    assert "ended" in body
    assert ended_assignment.assignment_status == "ended"


def test_branch_admin_teacher_registration_is_branch_scoped_and_rejects_cross_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Teacher Hidden Branch")
    director, _ = create_identity(
        academy_id=academy_id,
        email="teacher-scope-director@example.com",
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
            "email": director.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/teachers")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/teachers",
        data={
            "teacher_code": "WEB-T-A",
            "full_name": "Visible Teacher",
            "employment_status": "active",
            "specialization": "",
            "branch_id": str(branch_id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )
    page = client.get(f"/academies/{academy_id}/teachers")
    client.post(
        f"/academies/{academy_id}/teachers",
        data={
            "teacher_code": "WEB-T-B",
            "full_name": "Hidden Teacher",
            "employment_status": "active",
            "specialization": "",
            "branch_id": str(other_branch.id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(page.get_data(as_text=True)),
        },
    )
    client.post("/logout", data={"_csrf_token": _csrf_from_body(page.get_data(as_text=True))})

    admin, _ = create_identity(
        academy_id=academy_id,
        email="teacher-scope-admin@example.com",
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
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/teachers")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Visible Teacher" in body
    assert "Hidden Teacher" not in body

    denied = client.post(
        f"/academies/{academy_id}/teachers",
        data={
            "teacher_code": "WEB-T-X",
            "full_name": "Cross Branch Teacher",
            "employment_status": "active",
            "specialization": "",
            "branch_id": str(other_branch.id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


def test_academy_director_can_create_room_and_class_from_web(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="class-room-director@example.com",
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
    page = client.get(f"/academies/{academy_id}/classes")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Class and room setup" in body
    assert "Create room" in body
    assert "Create class" in body

    room_created = client.post(
        f"/academies/{academy_id}/rooms",
        data={
            "branch_id": str(branch_id),
            "room_code": "web-r-101",
            "room_name": "Web Room 101",
            "capacity": "16",
            "room_type": "Offline",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = room_created.get_data(as_text=True)

    assert room_created.status_code == 200
    assert "Room Web Room 101 berhasil dibuat." in body
    assert "WEB-R-101 / Offline" in body

    class_created = client.post(
        f"/academies/{academy_id}/classes",
        data={
            "branch_id": str(branch_id),
            "class_code": "web-c-7a",
            "class_name": "Web Class 7A",
            "capacity": "14",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = class_created.get_data(as_text=True)

    assert class_created.status_code == 200
    assert "Class Web Class 7A berhasil dibuat." in body
    assert "WEB-C-7A" in body

    room = db.session.scalar(db.select(Room).where(Room.room_code == "WEB-R-101"))
    academic_class = db.session.scalar(
        db.select(AcademicClass).where(AcademicClass.class_code == "WEB-C-7A")
    )

    assert room.branch_id == branch_id
    assert room.capacity == 16
    assert academic_class.branch_id == branch_id
    assert academic_class.capacity == 14


def test_branch_admin_class_room_setup_is_branch_scoped_and_rejects_cross_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Class Hidden Branch")
    director, _ = create_identity(
        academy_id=academy_id,
        email="class-room-seed-director@example.com",
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
            "email": director.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/classes")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/rooms",
        data={
            "branch_id": str(branch_id),
            "room_code": "VISIBLE-R",
            "room_name": "Visible Room",
            "capacity": "10",
            "room_type": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )
    page = client.get(f"/academies/{academy_id}/classes")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/classes",
        data={
            "branch_id": str(other_branch.id),
            "class_code": "HIDDEN-C",
            "class_name": "Hidden Class",
            "capacity": "10",
            "_csrf_token": _csrf_from_body(body),
        },
    )
    client.post("/logout", data={"_csrf_token": _csrf_from_body(body)})

    admin, _ = create_identity(
        academy_id=academy_id,
        email="class-room-admin@example.com",
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
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/classes")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Visible Room" in body
    assert "Hidden Class" not in body

    denied = client.post(
        f"/academies/{academy_id}/classes",
        data={
            "branch_id": str(other_branch.id),
            "class_code": "DENIED-C",
            "class_name": "Denied Class",
            "capacity": "8",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


def test_academy_director_can_create_student_user_profile_and_class_enrollment(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    user, _ = create_identity(
        academy_id=academy_id,
        email="student-flow-director@example.com",
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
    classes_page = client.get(f"/academies/{academy_id}/classes")
    body = classes_page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/classes",
        data={
            "branch_id": str(branch_id),
            "class_code": "STU-C-7A",
            "class_name": "Student Class 7A",
            "capacity": "12",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    page = client.get(f"/academies/{academy_id}/students")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Student registration" in body
    assert "Create student" in body

    created = client.post(
        f"/academies/{academy_id}/students",
        data={
            "student_code": "web-s-001",
            "full_name": "Web Student One",
            "birth_date": "2012-03-14",
            "home_branch_id": str(branch_id),
            "user_id": "",
            "user_email": "web-student-one@example.com",
            "user_password": "password12345",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)

    assert created.status_code == 200
    assert "Student Web Student One berhasil dibuat." in body
    assert "WEB-S-001" in body
    assert "web-student-one@example.com" in body
    assert "Class enrollment" in body

    student = db.session.scalar(
        db.select(Student).where(Student.student_code == "WEB-S-001")
    )
    academic_class = db.session.scalar(
        db.select(AcademicClass).where(AcademicClass.class_code == "STU-C-7A")
    )

    enrolled = client.post(
        f"/academies/{academy_id}/students/{student.id}/classes",
        data={
            "class_id": str(academic_class.id),
            "branch_id": str(branch_id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = enrolled.get_data(as_text=True)
    enrollment = db.session.scalar(
        db.select(ClassStudent).where(
            ClassStudent.student_id == student.id,
            ClassStudent.class_id == academic_class.id,
        )
    )

    assert enrolled.status_code == 200
    assert "Student berhasil dienroll ke class." in body
    assert "Student Class 7A" in body
    assert enrollment.enrollment_status == "active"


def test_branch_admin_student_registration_is_branch_scoped_and_rejects_cross_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Student Hidden Branch")
    director, _ = create_identity(
        academy_id=academy_id,
        email="student-scope-director@example.com",
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
            "email": director.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/students")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/students",
        data={
            "student_code": "VISIBLE-S",
            "full_name": "Visible Student",
            "birth_date": "",
            "home_branch_id": str(branch_id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )
    page = client.get(f"/academies/{academy_id}/students")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/students",
        data={
            "student_code": "HIDDEN-S",
            "full_name": "Hidden Student",
            "birth_date": "",
            "home_branch_id": str(other_branch.id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )
    client.post("/logout", data={"_csrf_token": _csrf_from_body(body)})

    admin, _ = create_identity(
        academy_id=academy_id,
        email="student-scope-admin@example.com",
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
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/students")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Visible Student" in body
    assert "Hidden Student" not in body

    denied = client.post(
        f"/academies/{academy_id}/students",
        data={
            "student_code": "DENIED-S",
            "full_name": "Denied Student",
            "birth_date": "",
            "home_branch_id": str(other_branch.id),
            "user_id": "",
            "user_email": "",
            "user_password": "",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


def test_academy_director_can_create_parent_link_children_and_revoke_link(
    client,
    create_identity,
    academy_id,
    branch_id,
):
    student_one = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="PARENT-LINK-1",
        full_name="Linked Child One",
        status="active",
    )
    student_two = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="PARENT-LINK-2",
        full_name="Linked Child Two",
        status="active",
    )
    db.session.add_all([student_one, student_two])
    user, _ = create_identity(
        academy_id=academy_id,
        email="parent-flow-director@example.com",
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
    page = client.get(f"/academies/{academy_id}/parents")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Parent registration" in body
    assert "Create parent" in body

    created = client.post(
        f"/academies/{academy_id}/parents",
        data={
            "full_name": "Web Parent One",
            "email": "web-parent-one@example.com",
            "password": "password12345",
            "relationship_type": "guardian",
            "primary_contact": "on",
            "student_id": str(student_one.id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)

    assert created.status_code == 200
    assert "Parent Web Parent One berhasil dibuat dan dihubungkan ke student." in body
    assert "Linked Child One" in body

    parent = db.session.scalar(
        db.select(Parent).join(User, User.id == Parent.user_id).where(
            User.email == "web-parent-one@example.com"
        )
    )
    linked = client.post(
        f"/academies/{academy_id}/parents/{parent.id}/students",
        data={
            "student_id": str(student_two.id),
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = linked.get_data(as_text=True)

    assert linked.status_code == 200
    assert "Parent-student link berhasil ditambahkan." in body
    assert "Linked Child Two" in body

    revoked = client.post(
        f"/academies/{academy_id}/parents/{parent.id}/students/{student_one.id}/revoke",
        data={"_csrf_token": _csrf_from_body(body)},
        follow_redirects=True,
    )
    body = revoked.get_data(as_text=True)
    inactive_link = db.session.scalar(
        db.select(ParentStudent).where(
            ParentStudent.parent_id == parent.id,
            ParentStudent.student_id == student_one.id,
        )
    )

    assert revoked.status_code == 200
    assert "Parent-student link berhasil dicabut." in body
    assert inactive_link.relationship_status == "inactive"

    api_login = client.post(
        "/api/v1/auth/login",
        json={
            "academy_id": str(academy_id),
            "email": "web-parent-one@example.com",
            "password": "password12345",
        },
    )
    headers = {"Authorization": f"Bearer {api_login.json['data']['access_token']}"}
    children = client.get("/api/v1/parent/children", headers=headers)
    allowed = client.get(
        f"/api/v1/parent/children/{student_two.id}/overview",
        headers=headers,
    )
    denied = client.get(
        f"/api/v1/parent/children/{student_one.id}/overview",
        headers=headers,
    )

    assert children.status_code == 200
    assert children.json["data"][0]["full_name"] == "Linked Child Two"
    assert allowed.status_code == 200
    assert denied.status_code == 403


def test_branch_admin_parent_registration_is_branch_scoped_and_rejects_cross_branch(
    client,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="Parent Hidden Branch")
    visible_student = Student(
        academy_id=academy_id,
        home_branch_id=branch_id,
        student_code="PARENT-VISIBLE",
        full_name="Parent Visible Child",
        status="active",
    )
    hidden_student = Student(
        academy_id=academy_id,
        home_branch_id=other_branch.id,
        student_code="PARENT-HIDDEN",
        full_name="Parent Hidden Child",
        status="active",
    )
    db.session.add_all([visible_student, hidden_student])
    director, _ = create_identity(
        academy_id=academy_id,
        email="parent-scope-director@example.com",
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
            "email": director.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/parents")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/parents",
        data={
            "full_name": "Visible Parent",
            "email": "visible-parent@example.com",
            "password": "password12345",
            "relationship_type": "guardian",
            "primary_contact": "on",
            "student_id": str(visible_student.id),
            "_csrf_token": _csrf_from_body(body),
        },
    )
    page = client.get(f"/academies/{academy_id}/parents")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/parents",
        data={
            "full_name": "Hidden Parent",
            "email": "hidden-parent@example.com",
            "password": "password12345",
            "relationship_type": "guardian",
            "primary_contact": "on",
            "student_id": str(hidden_student.id),
            "_csrf_token": _csrf_from_body(body),
        },
    )
    client.post("/logout", data={"_csrf_token": _csrf_from_body(body)})

    admin, _ = create_identity(
        academy_id=academy_id,
        email="parent-scope-admin@example.com",
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
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/parents")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Visible Parent" in body
    assert "Hidden Parent" not in body

    denied = client.post(
        f"/academies/{academy_id}/parents",
        data={
            "full_name": "Denied Parent",
            "email": "denied-parent@example.com",
            "password": "password12345",
            "relationship_type": "guardian",
            "primary_contact": "on",
            "student_id": str(hidden_student.id),
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()


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


def test_branch_admin_can_create_first_schedule_and_detail_from_web(
    client,
    identity,
    create_identity,
    academy_id,
    branch_id,
):
    context = _seed_schedule_ready_context(identity, academy_id, branch_id, suffix="CREATE")
    admin, _ = create_identity(
        academy_id=academy_id,
        email="cw9-admin-create@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/schedules")
    body = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "First schedule creation" in body
    assert "Conflict validation" in body

    created = client.post(
        f"/academies/{academy_id}/schedules",
        data={
            "branch_id": str(branch_id),
            "class_id": str(context["academic_class"].id),
            "teacher_id": str(context["teacher"].id),
            "room_id": str(context["room"].id),
            "starts_at": "2026-07-01T09:00",
            "ends_at": "2026-07-01T10:30",
            "timezone": "Asia/Jakarta",
            "status": "scheduled",
            "_csrf_token": _csrf_from_body(body),
        },
        follow_redirects=True,
    )
    body = created.get_data(as_text=True)
    schedule = db.session.scalar(
        db.select(Schedule).where(
            Schedule.academy_id == academy_id,
            Schedule.class_id == context["academic_class"].id,
        )
    )

    assert created.status_code == 200
    assert "Schedule pertama berhasil dibuat" in body
    assert "CW9 Class CREATE" in body
    assert "CW9 Teacher CREATE" in body
    assert "CW9 Room CREATE" in body
    assert schedule is not None
    assert schedule.session is not None
    assert schedule.session.status == "scheduled"


def test_schedule_creation_shows_conflict_validation_result(
    client,
    identity,
    create_identity,
    academy_id,
    branch_id,
):
    context = _seed_schedule_ready_context(identity, academy_id, branch_id, suffix="CONFLICT")
    admin, _ = create_identity(
        academy_id=academy_id,
        email="cw9-admin-conflict@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/schedules")
    body = page.get_data(as_text=True)
    payload = {
        "branch_id": str(branch_id),
        "class_id": str(context["academic_class"].id),
        "teacher_id": str(context["teacher"].id),
        "room_id": str(context["room"].id),
        "starts_at": "2026-07-02T09:00",
        "ends_at": "2026-07-02T10:30",
        "timezone": "Asia/Jakarta",
        "status": "scheduled",
        "_csrf_token": _csrf_from_body(body),
    }
    client.post(f"/academies/{academy_id}/schedules", data=payload)
    page = client.get(f"/academies/{academy_id}/schedules")
    payload["_csrf_token"] = _csrf_from_body(page.get_data(as_text=True))

    conflicted = client.post(
        f"/academies/{academy_id}/schedules",
        data=payload,
    )
    body = conflicted.get_data(as_text=True)

    assert conflicted.status_code == 409
    assert "Teacher already has an overlapping schedule." in body
    assert "Conflict stage: teacher / code: teacher_schedule_conflict." in body


def test_branch_admin_schedule_creation_rejects_cross_branch_resource(
    client,
    identity,
    create_identity,
    create_branch,
    academy_id,
    branch_id,
):
    other_branch = create_branch(academy_id=academy_id, name="CW9 Hidden Branch")
    visible = _seed_schedule_ready_context(identity, academy_id, branch_id, suffix="VISIBLE")
    hidden = _seed_schedule_ready_context(identity, academy_id, other_branch.id, suffix="HIDDEN")
    admin, _ = create_identity(
        academy_id=academy_id,
        email="cw9-admin-scope@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_ADMIN,
                "scope_type": ScopeType.BRANCH,
                "branch_id": branch_id,
            },
        ),
    )

    csrf = _csrf_from_login_page(client)
    client.post(
        "/login",
        data={
            "email": admin.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/schedules")
    body = page.get_data(as_text=True)

    assert "CW9 Class VISIBLE" in body
    assert "CW9 Class HIDDEN" not in body

    denied = client.post(
        f"/academies/{academy_id}/schedules",
        data={
            "branch_id": str(other_branch.id),
            "class_id": str(hidden["academic_class"].id),
            "teacher_id": str(hidden["teacher"].id),
            "room_id": str(hidden["room"].id),
            "starts_at": "2026-07-03T09:00",
            "ends_at": "2026-07-03T10:30",
            "timezone": "Asia/Jakarta",
            "status": "scheduled",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    assert denied.status_code == 403
    assert "permission" in denied.get_data(as_text=True).lower()
    assert visible["academic_class"].class_name == "CW9 Class VISIBLE"


def test_created_schedule_is_visible_on_role_dashboards(
    client,
    identity,
    create_identity,
    academy_id,
    branch_id,
):
    context = _seed_schedule_ready_context(identity, academy_id, branch_id, suffix="DASH")
    manager, _ = create_identity(
        academy_id=academy_id,
        email="cw9-manager-dashboard@example.com",
        password="password12345",
        assignments=(
            {
                "role": Role.BRANCH_MANAGER,
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
            "email": manager.email,
            "password": "password12345",
            "_csrf_token": csrf,
        },
    )
    page = client.get(f"/academies/{academy_id}/schedules")
    body = page.get_data(as_text=True)
    client.post(
        f"/academies/{academy_id}/schedules",
        data={
            "branch_id": str(branch_id),
            "class_id": str(context["academic_class"].id),
            "teacher_id": str(context["teacher"].id),
            "room_id": str(context["room"].id),
            "starts_at": "2026-07-04T09:00",
            "ends_at": "2026-07-04T10:30",
            "timezone": "Asia/Jakarta",
            "status": "scheduled",
            "_csrf_token": _csrf_from_body(body),
        },
    )

    for email, dashboard in [
        (manager.email, "/dashboard/branch_manager"),
        (context["teacher_user"].email, "/dashboard/teacher"),
        (context["student_user"].email, "/dashboard/student"),
        (context["parent_user"].email, "/dashboard/parent"),
    ]:
        with client.session_transaction() as session:
            session.clear()
        csrf = _csrf_from_login_page(client)
        client.post(
            "/login",
            data={
                "email": email,
                "password": "password12345",
                "_csrf_token": csrf,
            },
        )
        response = client.get(dashboard)
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Upcoming schedule" in body
        assert "CW9 Class DASH" in body
        assert "CW9 Teacher DASH" in body
        assert "CW9 Room DASH" in body


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
