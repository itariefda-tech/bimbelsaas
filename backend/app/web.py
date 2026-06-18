from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.common.responses import error_response
from app.common.errors import AuthenticationError
from app.models.academy import Academy
from app.models.branch import Branch
from app.models.user import User
from app.permissions.constants import Role
from app.services.auth_service import AuthService


CSRF_SESSION_KEY = "_csrf_token"

ROLE_LABELS = {
    Role.PLATFORM_OWNER: "Platform Owner",
    Role.ACADEMY_DIRECTOR: "Academy Director",
    Role.BRANCH_MANAGER: "Branch Manager",
    Role.BRANCH_ADMIN: "Branch Admin",
    Role.TEACHER: "Teacher",
    Role.PARENT: "Parent",
    Role.STUDENT: "Student",
}

ROLE_DESCRIPTIONS = {
    Role.PLATFORM_OWNER: "Global SaaS command center for academy health.",
    Role.ACADEMY_DIRECTOR: "Executive academy monitoring across branches.",
    Role.BRANCH_MANAGER: "Branch operational control and daily stability.",
    Role.BRANCH_ADMIN: "Fast branch workspace for schedules and operations.",
    Role.TEACHER: "Tactical daily workspace for teaching flow.",
    Role.PARENT: "Premium monitoring view for linked student activity.",
    Role.STUDENT: "Simple learning workspace for schedules and materials.",
}


@dataclass(frozen=True)
class DashboardContext:
    role: Role
    role_label: str
    description: str
    academy_name: str
    branch_name: str
    branch_count: int


def register_web(app: Flask) -> None:
    @app.context_processor
    def inject_security_helpers():
        return {
            "csrf_token": _csrf_token,
            "demo_login_hints_enabled": app.config["DEMO_LOGIN_HINTS_ENABLED"],
            "demo_password": app.config["DEMO_PASSWORD"],
        }

    @app.get("/")
    def index():
        if _current_principal() is not None:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login_page"))

    @app.get("/health")
    def root_health():
        return {
            "status": "ok",
            "app": "Premium Multi-Branch Academic Operations Platform",
        }

    @app.get("/login")
    def login_page():
        if _current_principal() is not None:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.post("/login")
    def login_submit():
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman login.", "error")
            return render_template("login.html", email=email), 400
        try:
            auth_payload = _web_login(email=email, password=password)
        except AuthenticationError:
            flash("Email atau password demo tidak valid.", "error")
            return render_template("login.html", email=email), 401

        session.clear()
        session["access_token"] = auth_payload["access_token"]
        session["refresh_token"] = auth_payload["refresh_token"]
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    def logout():
        if not _validate_csrf():
            return render_template("error.html", status_code=400), 400
        principal = _current_principal()
        if principal is not None:
            AuthService().logout(principal)
        session.clear()
        return redirect(url_for("login_page"))

    @app.get("/dashboard")
    def dashboard():
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        role = _first_role(principal)
        if role is None:
            flash("User belum memiliki role aktif.", "error")
            return redirect(url_for("login_page"))
        return redirect(url_for("dashboard_role", role=role.value))

    @app.get("/dashboard/<role>")
    def dashboard_role(role: str):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        selected_role = _parse_role(role)
        active_roles = _active_roles(principal)
        if selected_role is None or selected_role not in active_roles:
            return render_template("error.html", status_code=403), 403
        return render_template(
            "dashboard.html",
            user=principal.user,
            roles=active_roles,
            role_labels=ROLE_LABELS,
            context=_dashboard_context(principal, selected_role),
        )

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return error_response(
                message="The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
                code="not_found",
                status=404,
            )
        return render_template("error.html", status_code=404), 404

    @app.errorhandler(500)
    def server_error(_error):
        if request.path.startswith("/api/"):
            return error_response(
                message="An unexpected error occurred.",
                code="internal_server_error",
                status=500,
            )
        return render_template("error.html", status_code=500), 500


def _csrf_token() -> str:
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def _validate_csrf() -> bool:
    token = session.get(CSRF_SESSION_KEY)
    submitted = request.form.get(CSRF_SESSION_KEY, "")
    return bool(
        token
        and submitted
        and hmac.compare_digest(str(token), submitted)
    )


def _current_principal():
    token = session.get("access_token")
    if not token:
        return None
    try:
        return AuthService().authenticate_access_token(token)
    except AuthenticationError:
        session.clear()
        return None


def _web_login(*, email: str, password: str) -> dict[str, object]:
    service = AuthService()
    try:
        return service.login(email=email, password=password, academy_id=None)
    except AuthenticationError:
        normalized_email = email.strip().lower()
        users = User.query.filter_by(email=normalized_email, status="active").all()
        academy_users = [user for user in users if user.academy_id is not None]
        if len(academy_users) != 1:
            raise
        return service.login(
            email=email,
            password=password,
            academy_id=academy_users[0].academy_id,
        )


def _require_web_auth():
    principal = _current_principal()
    if principal is None:
        return None
    return principal


def _parse_role(value: str) -> Role | None:
    try:
        return Role(value)
    except ValueError:
        return None


def _active_roles(principal) -> list[Role]:
    roles = []
    for assignment in principal.assignments:
        role = _parse_role(assignment.role)
        if role is not None and role not in roles:
            roles.append(role)
    return roles


def _first_role(principal) -> Role | None:
    roles = _active_roles(principal)
    return roles[0] if roles else None


def _dashboard_context(principal, role: Role) -> DashboardContext:
    assignment = next(
        (
            item
            for item in principal.assignments
            if item.role == role.value
        ),
        None,
    )
    academy_id = getattr(assignment, "academy_id", None) or principal.user.academy_id
    branch_id = getattr(assignment, "branch_id", None)

    academy = Academy.query.get(academy_id) if academy_id else None
    branch = Branch.query.get(branch_id) if branch_id else None
    branch_count = (
        Branch.query.filter_by(academy_id=academy_id).count() if academy_id else 0
    )

    return DashboardContext(
        role=role,
        role_label=ROLE_LABELS[role],
        description=ROLE_DESCRIPTIONS[role],
        academy_name=academy.name if academy else "Platform Scope",
        branch_name=branch.name if branch else "All Branches",
        branch_count=branch_count,
    )
