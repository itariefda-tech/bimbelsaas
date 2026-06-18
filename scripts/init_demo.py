from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.academy import Academy  # noqa: E402
from app.models.branch import Branch  # noqa: E402
from app.models.parent import Parent  # noqa: E402
from app.models.parent_student import ParentStudent  # noqa: E402
from app.models.role_assignment import RoleAssignment  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.subscription import AcademySubscription, SaasPlan  # noqa: E402
from app.models.teacher import Teacher  # noqa: E402
from app.models.teacher_branch import TeacherBranch  # noqa: E402
from app.models.user import User  # noqa: E402
from app.permissions.constants import Role, ScopeType  # noqa: E402


PASSWORD = "password123"
DEMO_ACADEMY_SLUG = "demo-academy"
DEMO_BRANCH_CODE = "MAIN"


def main() -> None:
    app = create_app()
    if not app.config["DEMO_SEED_ENABLED"]:
        raise RuntimeError(
            "Demo seeding is disabled for this environment. "
            "Set APP_ENV=development or enable DEMO_SEED_ENABLED only in a safe sandbox."
        )
    global PASSWORD
    PASSWORD = app.config["DEMO_PASSWORD"]
    with app.app_context():
        db.create_all()
        academy = _academy()
        branch = _branch(academy)
        owner = _user(
            email="owner@example.com",
            full_name="Demo Platform Owner",
            academy_id=None,
            identity_scope="platform",
        )
        director = _user("director@example.com", "Demo Academy Director", academy.id)
        manager = _user("manager@example.com", "Demo Branch Manager", academy.id)
        admin = _user("admin@example.com", "Demo Branch Admin", academy.id)
        teacher_user = _user("teacher@example.com", "Demo Teacher", academy.id)
        parent_user = _user("parent@example.com", "Demo Parent", academy.id)
        student_user = _user("student@example.com", "Demo Student", academy.id)

        student = _student(academy, branch, student_user)
        _teacher(academy, branch, teacher_user)
        _parent(academy, parent_user, student)
        _plan_and_subscription(academy, owner)

        _role(owner, Role.PLATFORM_OWNER, ScopeType.PLATFORM)
        _role(director, Role.ACADEMY_DIRECTOR, ScopeType.ACADEMY, academy)
        _role(manager, Role.BRANCH_MANAGER, ScopeType.BRANCH, academy, branch)
        _role(admin, Role.BRANCH_ADMIN, ScopeType.BRANCH, academy, branch)
        _role(teacher_user, Role.TEACHER, ScopeType.BRANCH, academy, branch)
        _role(
            parent_user,
            Role.PARENT,
            ScopeType.LINKED_STUDENT,
            academy,
            branch,
            scope_id=student.id,
        )
        _role(
            student_user,
            Role.STUDENT,
            ScopeType.SELF,
            academy,
            branch,
            scope_id=student_user.id,
        )

        db.session.commit()
        print("Demo database is ready.")
        print("Run: python app.py")
        print(f"Demo password for all users: {PASSWORD}")


def _academy() -> Academy:
    academy = Academy.query.filter_by(slug=DEMO_ACADEMY_SLUG).one_or_none()
    if academy is None:
        academy = Academy(
            name="Demo Academy",
            slug=DEMO_ACADEMY_SLUG,
            timezone="Asia/Jakarta",
            currency="IDR",
            status="active",
        )
        db.session.add(academy)
        db.session.flush()
    return academy


def _branch(academy: Academy) -> Branch:
    branch = Branch.query.filter_by(
        academy_id=academy.id,
        code=DEMO_BRANCH_CODE,
    ).one_or_none()
    if branch is None:
        branch = Branch(
            academy_id=academy.id,
            name="Demo Main Branch",
            code=DEMO_BRANCH_CODE,
            timezone="Asia/Jakarta",
            status="active",
            address="Demo Academic Center",
        )
        db.session.add(branch)
        db.session.flush()
    return branch


def _user(
    email: str,
    full_name: str,
    academy_id=None,
    identity_scope: str = "academy",
) -> User:
    normalized_email = email.strip().lower()
    user = User.query.filter_by(
        academy_id=academy_id,
        email=normalized_email,
    ).one_or_none()
    if user is None:
        user = User(
            academy_id=academy_id,
            identity_scope=identity_scope,
            email=normalized_email,
            password_hash=generate_password_hash(PASSWORD),
            full_name=full_name,
            status="active",
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.password_hash = generate_password_hash(PASSWORD)
        user.full_name = full_name
        user.status = "active"
    return user


def _role(
    user: User,
    role: Role,
    scope_type: ScopeType,
    academy: Academy | None = None,
    branch: Branch | None = None,
    scope_id=None,
) -> RoleAssignment:
    if scope_type == ScopeType.PLATFORM:
        scope_key = "platform"
    elif scope_type == ScopeType.ACADEMY and academy is not None:
        scope_key = f"academy:{academy.id}"
        scope_id = academy.id
    elif scope_type == ScopeType.BRANCH and branch is not None:
        scope_key = f"branch:{branch.id}"
        scope_id = branch.id
    elif scope_type == ScopeType.LINKED_STUDENT and scope_id is not None:
        scope_key = f"linked_student:{scope_id}"
    elif scope_type == ScopeType.SELF and scope_id is not None:
        scope_key = f"self:{scope_id}"
    else:
        raise RuntimeError(f"Unsupported role scope for {role.value}.")

    assignment = RoleAssignment.query.filter_by(
        user_id=user.id,
        role=role.value,
        scope_key=scope_key,
    ).one_or_none()
    if assignment is None:
        assignment = RoleAssignment(
            user_id=user.id,
            role=role.value,
            scope_type=scope_type.value,
            scope_key=scope_key,
            academy_id=academy.id if academy else None,
            branch_id=branch.id if branch else None,
            scope_id=scope_id,
            status="active",
        )
        db.session.add(assignment)
    else:
        assignment.status = "active"
        assignment.scope_type = scope_type.value
        assignment.academy_id = academy.id if academy else None
        assignment.branch_id = branch.id if branch else None
        assignment.scope_id = scope_id
    return assignment


def _teacher(academy: Academy, branch: Branch, user: User) -> Teacher:
    teacher = Teacher.query.filter_by(
        academy_id=academy.id,
        user_id=user.id,
    ).one_or_none()
    if teacher is None:
        teacher = Teacher(
            academy_id=academy.id,
            user_id=user.id,
            teacher_code="T-DEMO",
            full_name=user.full_name,
            employment_status="active",
            status="active",
        )
        db.session.add(teacher)
        db.session.flush()
    assignment = TeacherBranch.query.filter_by(
        academy_id=academy.id,
        teacher_id=teacher.id,
        branch_id=branch.id,
    ).one_or_none()
    if assignment is None:
        db.session.add(
            TeacherBranch(
                academy_id=academy.id,
                teacher_id=teacher.id,
                branch_id=branch.id,
                assignment_status="active",
            )
        )
    return teacher


def _student(academy: Academy, branch: Branch, user: User) -> Student:
    student = Student.query.filter_by(
        academy_id=academy.id,
        user_id=user.id,
    ).one_or_none()
    if student is None:
        student = Student(
            academy_id=academy.id,
            home_branch_id=branch.id,
            user_id=user.id,
            student_code="S-DEMO",
            full_name=user.full_name,
            status="active",
        )
        db.session.add(student)
        db.session.flush()
    return student


def _parent(academy: Academy, user: User, student: Student) -> Parent:
    parent = Parent.query.filter_by(
        academy_id=academy.id,
        user_id=user.id,
    ).one_or_none()
    if parent is None:
        parent = Parent(
            academy_id=academy.id,
            user_id=user.id,
            relationship_type="guardian",
            primary_contact=True,
            status="active",
        )
        db.session.add(parent)
        db.session.flush()
    link = ParentStudent.query.filter_by(
        academy_id=academy.id,
        parent_id=parent.id,
        student_id=student.id,
    ).one_or_none()
    if link is None:
        db.session.add(
            ParentStudent(
                academy_id=academy.id,
                parent_id=parent.id,
                student_id=student.id,
                relationship_status="active",
            )
        )
    return parent


def _plan_and_subscription(academy: Academy, owner: User) -> None:
    plan = SaasPlan.query.filter_by(code="demo").one_or_none()
    if plan is None:
        plan = SaasPlan(
            code="demo",
            name="Demo Professional",
            price_minor=0,
            currency="IDR",
            billing_interval="monthly",
            features=["runnable_mvp", "multi_branch_ready"],
            is_active=True,
        )
        db.session.add(plan)
        db.session.flush()
    subscription = AcademySubscription.query.filter_by(
        academy_id=academy.id,
    ).one_or_none()
    if subscription is None:
        now = datetime.now(timezone.utc)
        db.session.add(
            AcademySubscription(
                academy_id=academy.id,
                plan_id=plan.id,
                status="active",
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                created_by=owner.id,
            )
        )


if __name__ == "__main__":
    main()
