from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass
from uuid import UUID

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.common.errors import AppError
from app.common.responses import error_response
from app.common.errors import AuthenticationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.extensions import db
from app.models.academy import Academy
from app.models.branch import Branch
from app.models.user import User
from app.permissions.constants import Permission, Role, ScopeType
from app.repositories.role_assignment_repository import RoleAssignmentRepository
from app.repositories.user_repository import UserRepository
from app.services.academy_service import AcademyService
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService
from app.services.branch_service import BranchService
from app.permissions.context import AuthorizationTarget
from app.services.identity_service import IdentityService


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
    character: str
    academy_name: str
    branch_name: str
    branch_count: int
    metrics: list[dict[str, str]]
    focus_items: list[dict[str, str]]
    quick_actions: list[str]
    status_badge: str
    workflow_title: str
    workflow_items: list[dict[str, str]]
    state_title: str
    state_items: list[dict[str, str]]


ROLE_UI = {
    Role.PLATFORM_OWNER: {
        "character": "Global SaaS command center",
        "status_badge": "Platform ready",
        "metrics": [
            {"label": "Academy Scope", "value": "All academies", "tone": "navy"},
            {"label": "Staging Gate", "value": "Billing blocked", "tone": "amber"},
            {"label": "Runtime", "value": "Flask shell", "tone": "green"},
            {"label": "Next Focus", "value": "CI unlock", "tone": "slate"},
        ],
        "focus_items": [
            {
                "title": "SaaS health",
                "body": "Use this shell to confirm platform availability, environment readiness, and release blockers.",
            },
            {
                "title": "Production gate",
                "body": "CI billing and PostgreSQL staging validation remain the main external gates before customer-facing UI expansion.",
            },
        ],
        "quick_actions": [
            "Register tenant",
            "Review staging runbook",
            "Check CI blocker",
            "Prepare release checklist",
        ],
        "workflow_title": "Connected SaaS setup",
        "workflow_items": [
            {
                "label": "Tenant",
                "title": "Register a new academy tenant",
                "body": "Start the connected SaaS flow by creating the academy identity before branches, roles, people, schedules, and billing.",
                "status": "Next",
            },
            {
                "label": "Setup",
                "title": "Prepare branch and internal roles",
                "body": "After the tenant exists, add branch scope and assign director, manager, and assistant roles.",
                "status": "Queued",
            },
        ],
        "state_title": "Tenant onboarding states",
        "state_items": [
            {
                "label": "Empty",
                "title": "No tenant selected",
                "body": "Create or choose an academy before continuing setup work.",
            },
            {
                "label": "Error",
                "title": "Tenant cannot be created",
                "body": "Show duplicate slug, invalid timezone, and missing field messages without losing entered form data.",
            },
            {
                "label": "Denied",
                "title": "Platform owner only",
                "body": "Tenant registration is blocked for academy and branch-scoped roles.",
            },
            {
                "label": "Success",
                "title": "Tenant ready for setup",
                "body": "Move next to academy profile, branch setup, and internal role assignment.",
            },
        ],
    },
    Role.ACADEMY_DIRECTOR: {
        "character": "Executive academy monitoring",
        "status_badge": "Academy stable",
        "metrics": [
            {"label": "Academy", "value": "{academy_name}", "tone": "navy"},
            {"label": "Branches", "value": "{branch_count}", "tone": "green"},
            {"label": "Visibility", "value": "All branches", "tone": "slate"},
            {"label": "Priority", "value": "Branch health", "tone": "amber"},
        ],
        "focus_items": [
            {
                "title": "Branch overview",
                "body": "Monitor branch operations from a calm executive view before drilling into daily details.",
            },
            {
                "title": "Operational alerts",
                "body": "Revenue, attendance, teacher load, and schedule stability should become the director dashboard core.",
            },
        ],
        "quick_actions": ["Review branch summary", "Compare branch health", "Check pending risks"],
    },
    Role.BRANCH_MANAGER: {
        "character": "Branch operational control",
        "status_badge": "Branch ready",
        "metrics": [
            {"label": "Branch", "value": "{branch_name}", "tone": "navy"},
            {"label": "Schedule", "value": "Stable", "tone": "green"},
            {"label": "Approvals", "value": "Review queue", "tone": "amber"},
            {"label": "Scope", "value": "Branch team", "tone": "slate"},
        ],
        "focus_items": [
            {
                "title": "Today operations",
                "body": "Keep schedule stability, teacher coverage, and parent-facing commitments visible.",
            },
            {
                "title": "Approval flow",
                "body": "Reschedule, attendance correction, and lesson summary correction queues should stay fast and auditable.",
            },
        ],
        "quick_actions": ["Open today board", "Review approvals", "Check teacher load"],
    },
    Role.BRANCH_ADMIN: {
        "character": "Fast operational workspace",
        "status_badge": "Ops ready",
        "metrics": [
            {"label": "Branch", "value": "{branch_name}", "tone": "navy"},
            {"label": "Search", "value": "Ready", "tone": "green"},
            {"label": "Queue", "value": "Operational", "tone": "amber"},
            {"label": "Mode", "value": "Fast admin", "tone": "slate"},
        ],
        "focus_items": [
            {
                "title": "Quick operations",
                "body": "The admin shell should prioritize search, schedule edits, invoice support, and attendance support.",
            },
            {
                "title": "Conflict prevention",
                "body": "Surface schedule conflict indicators and missing operational data before they become parent-facing issues.",
            },
        ],
        "quick_actions": [
            "Search student",
            "Update schedule",
            "Support attendance",
            "Check invoices",
        ],
        "workflow_title": "Branch admin operations flow",
        "workflow_items": [
            {
                "label": "Search",
                "title": "Find the student, parent, class, or invoice first",
                "body": "Start from a single branch-scoped search so admin work stays fast and avoids cross-branch data leaks.",
                "status": "Primary",
            },
            {
                "label": "Schedule",
                "title": "Review operational schedule changes",
                "body": "Check room, teacher, and class conflicts before creating edits that become parent-visible.",
                "status": "Guarded",
            },
            {
                "label": "Attendance",
                "title": "Support attendance corrections",
                "body": "Help teachers and managers find missing or disputed attendance records without silently changing history.",
                "status": "Audited",
            },
            {
                "label": "Invoice",
                "title": "Answer payment and invoice questions",
                "body": "Keep invoice amount, due date, payment proof, and status clear before escalating finance exceptions.",
                "status": "Support",
            },
            {
                "label": "Queue",
                "title": "Close pending operations cleanly",
                "body": "Use one queue for incomplete schedules, missing student data, invoice questions, and attendance follow-ups.",
                "status": "Daily",
            },
        ],
        "state_title": "Branch admin operational states",
        "state_items": [
            {
                "label": "Empty",
                "title": "No branch records found",
                "body": "Show an actionable empty state for search, schedule, invoice, or attendance results.",
            },
            {
                "label": "Loading",
                "title": "Checking branch data",
                "body": "Use compact skeleton rows so admins can keep context while schedule or search data refreshes.",
            },
            {
                "label": "Error",
                "title": "Operation could not complete",
                "body": "Preserve entered search or form data and explain the next retry or escalation step.",
            },
            {
                "label": "Denied",
                "title": "Outside branch scope",
                "body": "Block access to other branch records and keep the admin anchored to their assigned branch.",
            },
        ],
    },
    Role.TEACHER: {
        "character": "Tactical daily workspace",
        "status_badge": "Class day ready",
        "metrics": [
            {"label": "Today", "value": "Timeline", "tone": "navy"},
            {"label": "Next Class", "value": "Focus", "tone": "green"},
            {"label": "Materials", "value": "Ready queue", "tone": "slate"},
            {"label": "Attendance", "value": "Shortcut", "tone": "amber"},
        ],
        "focus_items": [
            {
                "title": "Next class focus",
                "body": "Teacher UI should start with what happens next, not with generic administration.",
            },
            {
                "title": "Low-friction teaching",
                "body": "Attendance, materials, and lesson summary actions should be reachable in one clear step.",
            },
        ],
        "quick_actions": ["Open timeline", "Take attendance", "Write lesson summary"],
        "workflow_title": "Today teaching flow",
        "workflow_items": [
            {
                "label": "Next class",
                "title": "Start from the next scheduled session",
                "body": "Review class, branch, room, and material readiness before opening attendance.",
                "status": "Primary",
            },
            {
                "label": "Attendance",
                "title": "Record attendance during class",
                "body": "Keep draft attendance lightweight, then finalize once the roster is complete.",
                "status": "Shortcut",
            },
            {
                "label": "Lesson summary",
                "title": "Publish a clear parent-facing summary",
                "body": "Capture topic, class summary, homework, and attention notes after the session.",
                "status": "After class",
            },
        ],
    },
    Role.PARENT: {
        "character": "Premium monitoring experience",
        "status_badge": "Child view ready",
        "metrics": [
            {"label": "Child", "value": "Linked profile", "tone": "navy"},
            {"label": "Schedule", "value": "Transparent", "tone": "green"},
            {"label": "Progress", "value": "Visible", "tone": "slate"},
            {"label": "Trust", "value": "Calm updates", "tone": "amber"},
        ],
        "focus_items": [
            {
                "title": "Parent trust",
                "body": "Parent UI should feel reassuring: schedule, attendance, progress, invoice, and lesson notes in plain language.",
            },
            {
                "title": "Clear monitoring",
                "body": "Prioritize readable activity history and calm notification hierarchy over dense admin controls.",
            },
        ],
        "quick_actions": ["View child overview", "Check schedule", "Review invoices"],
        "workflow_title": "Monitoring flow",
        "workflow_items": [
            {
                "label": "Child overview",
                "title": "Start with current learning status",
                "body": "Surface linked child profile, branch, active class, attendance, and learning progress in one calm view.",
                "status": "Primary",
            },
            {
                "label": "Activity feed",
                "title": "Show meaningful academic activity",
                "body": "Keep attendance, class start, homework, and lesson completion updates chronological and readable.",
                "status": "Trust",
            },
            {
                "label": "Schedule",
                "title": "Keep upcoming sessions transparent",
                "body": "Show upcoming sessions, teacher, room, cancellations, and reschedules clearly so parents never guess.",
                "status": "Trust",
            },
            {
                "label": "Invoice",
                "title": "Make billing easy to understand",
                "body": "Expose amount, due date, payment status, and history without mixing finance with admin controls.",
                "status": "Clear",
            },
            {
                "label": "Progress",
                "title": "Explain momentum in human language",
                "body": "Use supportive attendance, milestone, and assignment signals instead of cold analytics tables.",
                "status": "Calm",
            },
        ],
        "state_title": "Parent trust states",
        "state_items": [
            {
                "label": "Empty",
                "title": "No linked child yet",
                "body": "Explain that academy staff must link the student before any private data appears.",
            },
            {
                "label": "Loading",
                "title": "Refreshing latest updates",
                "body": "Use a quiet skeleton state for schedule, invoice, attendance, and lesson summary refreshes.",
            },
            {
                "label": "Error",
                "title": "Latest data could not load",
                "body": "Keep the last trusted view visible and ask the parent to retry without exposing technical details.",
            },
            {
                "label": "Denied",
                "title": "Only linked students are visible",
                "body": "Block access to other student data and point the parent back to their child overview.",
            },
        ],
    },
    Role.STUDENT: {
        "character": "Simple learning workspace",
        "status_badge": "Learning ready",
        "metrics": [
            {"label": "Schedule", "value": "Upcoming", "tone": "navy"},
            {"label": "Materials", "value": "Available", "tone": "green"},
            {"label": "Progress", "value": "Simple", "tone": "slate"},
            {"label": "Focus", "value": "Learn next", "tone": "amber"},
        ],
        "focus_items": [
            {
                "title": "Learning clarity",
                "body": "Student UI should show what to attend, what to study, and what changed.",
            },
            {
                "title": "Simple actions",
                "body": "Avoid finance-heavy or admin-heavy information in the student workspace.",
            },
        ],
        "quick_actions": ["Check next class", "Open materials", "Review progress"],
        "workflow_title": "Learning flow",
        "workflow_items": [
            {
                "label": "Next class",
                "title": "Know what comes next",
                "body": "Keep schedule and materials simple, clear, and distraction-free.",
                "status": "Primary",
            },
        ],
    },
}


for role, config in ROLE_UI.items():
    config.setdefault("workflow_title", "Operational flow")
    config.setdefault(
        "workflow_items",
        [
            {
                "label": "Control",
                "title": config["character"],
                "body": "Use this control shell to inspect the role scope and prepare the next production workflow.",
                "status": "Ready",
            },
        ],
    )
    config.setdefault("state_title", "Operational states")
    config.setdefault(
        "state_items",
        [
            {
                "label": "Ready",
                "title": "Role scope available",
                "body": "This shell keeps the role workspace visible while deeper workflow screens are prepared.",
            },
        ],
    )


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

    @app.get("/tenants")
    def tenant_registration_page():
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        if not _is_platform_owner(principal):
            return render_template("error.html", user=principal.user, status_code=403), 403
        return _render_tenants(principal)

    @app.post("/tenants")
    def tenant_registration_submit():
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        if not _is_platform_owner(principal):
            return render_template("error.html", user=principal.user, status_code=403), 403
        form = _tenant_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman tenant registration.", "error")
            return _render_tenants(principal, form=form, status_code=400)
        try:
            academy = AcademyService().create(
                principal,
                name=form["name"],
                slug=form["slug"],
                timezone_name=form["timezone"],
                currency=form["currency"],
                logo_url=form["logo_url"],
            )
        except AppError as error:
            flash(error.message, "error")
            return _render_tenants(
                principal,
                form=form,
                status_code=error.status_code,
            )

        flash(f"Tenant {academy.name} berhasil dibuat.", "success")
        return redirect(url_for("tenant_registration_page"))

    @app.get("/academies/<uuid:academy_id>/setup")
    def academy_setup_page(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        return _render_academy_setup(principal, academy_id)

    @app.get("/academies/<uuid:academy_id>/team")
    def internal_team_page(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        return _render_internal_team(principal, academy_id)

    @app.post("/academies/<uuid:academy_id>/setup")
    def academy_setup_submit(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        form = _academy_setup_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman academy setup.", "error")
            return _render_academy_setup(
                principal,
                academy_id,
                academy_form=form,
                status_code=400,
            )
        try:
            academy = AcademyService().update(principal, academy_id, form)
        except AppError as error:
            flash(error.message, "error")
            return _render_academy_setup(
                principal,
                academy_id,
                academy_form=form,
                status_code=error.status_code,
            )
        flash(f"Academy {academy.name} berhasil diperbarui.", "success")
        return redirect(url_for("academy_setup_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/branches")
    def branch_setup_submit(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        form = _branch_setup_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman branch setup.", "error")
            return _render_academy_setup(
                principal,
                academy_id,
                branch_form=form,
                status_code=400,
            )
        try:
            branch = BranchService().create(
                principal,
                academy_id,
                name=form["name"],
                code=form["code"],
                timezone_name=form["timezone"],
                address=form["address"],
            )
        except AppError as error:
            flash(error.message, "error")
            return _render_academy_setup(
                principal,
                academy_id,
                branch_form=form,
                status_code=error.status_code,
            )
        flash(f"Branch {branch.name} berhasil dibuat.", "success")
        return redirect(url_for("academy_setup_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/branches/<uuid:branch_id>")
    def branch_update_submit(academy_id, branch_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        form = _branch_update_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman branch setup.", "error")
            return _render_academy_setup(
                principal,
                academy_id,
                status_code=400,
            )
        try:
            branch = BranchService().get_visible(principal, branch_id)
            if branch.academy_id != academy_id:
                raise AppError("Branch was not found.", code="not_found", status_code=404)
            BranchService().update(principal, branch_id, form)
        except AppError as error:
            flash(error.message, "error")
            return _render_academy_setup(
                principal,
                academy_id,
                status_code=error.status_code,
            )
        flash(f"Branch {form['name']} berhasil diperbarui.", "success")
        return redirect(url_for("academy_setup_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/branches/<uuid:branch_id>/archive")
    def branch_archive_submit(academy_id, branch_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman branch setup.", "error")
            return _render_academy_setup(
                principal,
                academy_id,
                status_code=400,
            )
        try:
            branch = BranchService().get_visible(principal, branch_id)
            if branch.academy_id != academy_id:
                raise AppError("Branch was not found.", code="not_found", status_code=404)
            archived = BranchService().archive(principal, branch_id)
        except AppError as error:
            flash(error.message, "error")
            return _render_academy_setup(
                principal,
                academy_id,
                status_code=error.status_code,
            )
        flash(f"Branch {archived.name} berhasil diarsipkan.", "success")
        return redirect(url_for("academy_setup_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/team/users")
    def internal_user_create_submit(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        form = _internal_user_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman internal team.", "error")
            return _render_internal_team(
                principal,
                academy_id,
                user_form=form,
                status_code=400,
            )
        try:
            _require_permission(
                principal,
                Permission.USER_CREATE,
                AuthorizationTarget(academy_id=academy_id),
            )
            _require_permission(
                principal,
                Permission.ROLE_ASSIGN,
                _role_assignment_target(academy_id, form["role"], form["branch_id"]),
            )
            service = IdentityService()
            user = service.create_user(
                email=form["email"],
                password=form["password"],
                full_name=form["full_name"],
                academy_id=academy_id,
            )
            service.assign_role(
                user=user,
                role=Role(form["role"]),
                scope_type=_internal_scope_type(form["role"]),
                academy_id=academy_id,
                branch_id=form["branch_id"] or None,
                assigned_by=principal.user.id,
            )
            db.session.commit()
        except AppError as error:
            db.session.rollback()
            flash(error.message, "error")
            return _render_internal_team(
                principal,
                academy_id,
                user_form=form,
                status_code=error.status_code,
            )
        except ValueError:
            db.session.rollback()
            flash("Internal role selection is invalid.", "error")
            return _render_internal_team(
                principal,
                academy_id,
                user_form=form,
                status_code=422,
            )
        flash(f"Internal user {form['full_name']} berhasil dibuat dan diberi role.", "success")
        return redirect(url_for("internal_team_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/team/assignments")
    def internal_role_assign_submit(academy_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        form = _internal_assignment_form()
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman internal team.", "error")
            return _render_internal_team(
                principal,
                academy_id,
                assignment_form=form,
                status_code=400,
            )
        try:
            _require_permission(
                principal,
                Permission.ROLE_ASSIGN,
                _role_assignment_target(academy_id, form["role"], form["branch_id"]),
            )
            user = UserRepository().get_active_by_id(form["user_id"])
            if user is None or user.academy_id != academy_id:
                raise AppError("User was not found in this academy.", code="not_found", status_code=404)
            IdentityService().assign_role(
                user=user,
                role=Role(form["role"]),
                scope_type=_internal_scope_type(form["role"]),
                academy_id=academy_id,
                branch_id=form["branch_id"] or None,
                assigned_by=principal.user.id,
            )
            db.session.commit()
        except AppError as error:
            db.session.rollback()
            flash(error.message, "error")
            return _render_internal_team(
                principal,
                academy_id,
                assignment_form=form,
                status_code=error.status_code,
            )
        except ValueError:
            db.session.rollback()
            flash("Internal role selection is invalid.", "error")
            return _render_internal_team(
                principal,
                academy_id,
                assignment_form=form,
                status_code=422,
            )
        flash("Internal role berhasil ditambahkan.", "success")
        return redirect(url_for("internal_team_page", academy_id=academy_id))

    @app.post("/academies/<uuid:academy_id>/team/assignments/<uuid:assignment_id>/revoke")
    def internal_role_revoke_submit(academy_id, assignment_id):
        principal = _require_web_auth()
        if principal is None:
            return redirect(url_for("login_page"))
        if not _validate_csrf():
            flash("Sesi form tidak valid. Muat ulang halaman internal team.", "error")
            return _render_internal_team(
                principal,
                academy_id,
                status_code=400,
            )
        try:
            assignment = RoleAssignmentRepository().get_by_id(assignment_id)
            if assignment is None or assignment.academy_id != academy_id:
                raise AppError("Role assignment was not found.", code="not_found", status_code=404)
            _require_permission(
                principal,
                Permission.ROLE_REVOKE,
                AuthorizationTarget(
                    academy_id=assignment.academy_id,
                    branch_id=assignment.branch_id,
                ),
            )
            IdentityService().revoke_role(assignment, revoked_by=principal.user.id)
            db.session.commit()
        except AppError as error:
            db.session.rollback()
            flash(error.message, "error")
            return _render_internal_team(
                principal,
                academy_id,
                status_code=error.status_code,
            )
        flash("Internal role berhasil dicabut.", "success")
        return redirect(url_for("internal_team_page", academy_id=academy_id))

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


def _is_platform_owner(principal) -> bool:
    return Role.PLATFORM_OWNER in _active_roles(principal)


def _tenant_form() -> dict[str, str]:
    return {
        "name": request.form.get("name", "").strip(),
        "slug": request.form.get("slug", "").strip().lower(),
        "timezone": request.form.get("timezone", "Asia/Jakarta").strip(),
        "currency": request.form.get("currency", "IDR").strip().upper(),
        "logo_url": request.form.get("logo_url", "").strip(),
    }


def _academy_setup_form() -> dict[str, str]:
    form = {
        "name": request.form.get("name", "").strip(),
        "slug": request.form.get("slug", "").strip().lower(),
        "timezone": request.form.get("timezone", "").strip(),
        "currency": request.form.get("currency", "").strip().upper(),
        "logo_url": request.form.get("logo_url", "").strip(),
    }
    if "status" in request.form:
        form["status"] = request.form.get("status", "").strip()
    return form


def _branch_setup_form() -> dict[str, str]:
    return {
        "name": request.form.get("name", "").strip(),
        "code": request.form.get("code", "").strip().upper(),
        "timezone": request.form.get("timezone", "Asia/Jakarta").strip(),
        "address": request.form.get("address", "").strip(),
    }


def _branch_update_form() -> dict[str, str]:
    return {
        "name": request.form.get("name", "").strip(),
        "code": request.form.get("code", "").strip().upper(),
        "timezone": request.form.get("timezone", "").strip(),
        "address": request.form.get("address", "").strip(),
        "status": request.form.get("status", "").strip(),
    }


def _internal_user_form() -> dict[str, object]:
    return {
        "full_name": request.form.get("full_name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "password": request.form.get("password", "").strip(),
        "role": request.form.get("role", Role.ACADEMY_DIRECTOR.value).strip(),
        "branch_id": _optional_uuid(request.form.get("branch_id", "").strip()),
    }


def _internal_assignment_form() -> dict[str, object]:
    return {
        "user_id": _required_uuid(request.form.get("user_id", "").strip()),
        "role": request.form.get("role", Role.ACADEMY_DIRECTOR.value).strip(),
        "branch_id": _optional_uuid(request.form.get("branch_id", "").strip()),
    }


def _optional_uuid(value: str) -> UUID | None:
    if not value:
        return None
    return _required_uuid(value)


def _required_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise AppError("Selected record is invalid.", code="validation_error", status_code=422) from error


def _render_tenants(principal, *, form: dict[str, str] | None = None, status_code: int = 200):
    academies = AcademyService().list_visible(principal)
    default_form = {
        "name": "",
        "slug": "",
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "logo_url": "",
    }
    return (
        render_template(
            "tenants.html",
            user=principal.user,
            academies=academies,
            form=form or default_form,
        ),
        status_code,
    )


def _render_academy_setup(
    principal,
    academy_id,
    *,
    academy_form: dict[str, str] | None = None,
    branch_form: dict[str, str] | None = None,
    status_code: int = 200,
):
    academy_service = AcademyService()
    branch_service = BranchService()
    try:
        academy = academy_service.get_visible(principal, academy_id)
        branches = branch_service.list_visible(principal, academy_id)
    except AppError as error:
        return render_template(
            "error.html",
            user=principal.user,
            status_code=error.status_code,
        ), error.status_code

    default_academy_form = {
        "name": academy.name,
        "slug": academy.slug,
        "timezone": academy.timezone,
        "currency": academy.currency,
        "logo_url": academy.logo_url or "",
        "status": academy.status,
    }
    default_branch_form = {
        "name": "",
        "code": "",
        "timezone": academy.timezone,
        "address": "",
    }
    return (
        render_template(
            "academy_setup.html",
            user=principal.user,
            academy=academy,
            branches=branches,
            academy_form=academy_form or default_academy_form,
            branch_form=branch_form or default_branch_form,
            academy_statuses=[status.value for status in AcademyStatus],
            branch_statuses=[
                BranchStatus.ACTIVE.value,
                BranchStatus.INACTIVE.value,
                BranchStatus.MAINTENANCE.value,
                BranchStatus.SUSPENDED.value,
            ],
            can_manage_academy=_can_manage_academy(principal, academy.id),
            can_manage_lifecycle=_can_manage_platform(principal),
            can_access_tenants=_is_platform_owner(principal),
            can_create_branch=_can_create_branch(principal, academy.id),
            archived_academy=academy.status == AcademyStatus.ARCHIVED,
            readonly_academy=(
                academy.status == AcademyStatus.ARCHIVED
                or (
                    academy.status == AcademyStatus.SUSPENDED
                    and not _can_manage_platform(principal)
                )
            ),
            can_edit_branch=lambda branch: _can_edit_branch(principal, branch),
            can_archive_branch=lambda branch: _can_archive_branch(principal, branch),
        ),
        status_code,
    )


def _render_internal_team(
    principal,
    academy_id,
    *,
    user_form: dict[str, object] | None = None,
    assignment_form: dict[str, object] | None = None,
    status_code: int = 200,
):
    try:
        academy = AcademyService().get_visible(principal, academy_id)
        _require_permission(
            principal,
            Permission.USER_VIEW,
            AuthorizationTarget(academy_id=academy.id),
        )
        branches = BranchService().list_visible(principal, academy.id)
    except AppError as error:
        return render_template(
            "error.html",
            user=principal.user,
            status_code=error.status_code,
        ), error.status_code

    visible_branch_ids = {branch.id for branch in branches}
    users = UserRepository().list_active_for_academy(academy.id)
    assignments = [
        assignment
        for assignment in RoleAssignmentRepository().list_active_for_academy(academy.id)
        if assignment.role in _internal_role_values()
        and (
            assignment.branch_id is None
            or assignment.branch_id in visible_branch_ids
        )
    ]
    branch_by_id = {branch.id: branch for branch in branches}
    default_user_form = {
        "full_name": "",
        "email": "",
        "password": "",
        "role": Role.ACADEMY_DIRECTOR.value,
        "branch_id": "",
    }
    default_assignment_form = {
        "user_id": "",
        "role": Role.ACADEMY_DIRECTOR.value,
        "branch_id": "",
    }
    return (
        render_template(
            "internal_team.html",
            user=principal.user,
            academy=academy,
            branches=branches,
            users=users,
            assignments=assignments,
            branch_by_id=branch_by_id,
            role_labels=ROLE_LABELS,
            role_name_by_value={role.value: ROLE_LABELS[role] for role in Role},
            internal_roles=_internal_roles(),
            user_form=user_form or default_user_form,
            assignment_form=assignment_form or default_assignment_form,
            can_create_user=_can_create_user(principal, academy.id),
            can_assign_role=_can_assign_role(principal, academy.id),
            can_revoke_role=lambda assignment: _can_revoke_role(principal, assignment),
            can_access_tenants=_is_platform_owner(principal),
        ),
        status_code,
    )


def _internal_roles() -> list[Role]:
    return [
        Role.ACADEMY_DIRECTOR,
        Role.BRANCH_MANAGER,
        Role.BRANCH_ADMIN,
    ]


def _internal_role_values() -> set[str]:
    return {role.value for role in _internal_roles()}


def _internal_scope_type(role: str) -> ScopeType:
    selected = Role(role)
    if selected == Role.ACADEMY_DIRECTOR:
        return ScopeType.ACADEMY
    if selected in {Role.BRANCH_MANAGER, Role.BRANCH_ADMIN}:
        return ScopeType.BRANCH
    raise ValueError(role)


def _role_assignment_target(academy_id, role: str, branch_id: UUID | None) -> AuthorizationTarget:
    scope_type = _internal_scope_type(role)
    return AuthorizationTarget(
        academy_id=academy_id,
        branch_id=branch_id if scope_type == ScopeType.BRANCH else None,
    )


def _require_permission(principal, permission: Permission, target: AuthorizationTarget) -> None:
    AuthorizationService.require(principal, permission, target)


def _can_manage_platform(principal) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.PLATFORM_MANAGE,
        AuthorizationTarget(),
    )


def _can_manage_academy(principal, academy_id) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.ACADEMY_MANAGE,
        AuthorizationTarget(academy_id=academy_id),
    )


def _can_create_branch(principal, academy_id) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.BRANCH_CREATE,
        AuthorizationTarget(academy_id=academy_id),
    )


def _can_create_user(principal, academy_id) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.USER_CREATE,
        AuthorizationTarget(academy_id=academy_id),
    )


def _can_assign_role(principal, academy_id) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.ROLE_ASSIGN,
        AuthorizationTarget(academy_id=academy_id),
    )


def _can_revoke_role(principal, assignment) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.ROLE_REVOKE,
        AuthorizationTarget(
            academy_id=assignment.academy_id,
            branch_id=assignment.branch_id,
        ),
    )


def _can_edit_branch(principal, branch: Branch) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.BRANCH_EDIT,
        AuthorizationTarget(academy_id=branch.academy_id, branch_id=branch.id),
    )


def _can_archive_branch(principal, branch: Branch) -> bool:
    return AuthorizationService.is_allowed(
        principal,
        Permission.BRANCH_ARCHIVE,
        AuthorizationTarget(academy_id=branch.academy_id, branch_id=branch.id),
    )


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
        character=ROLE_UI[role]["character"],
        academy_name=academy.name if academy else "Platform Scope",
        branch_name=branch.name if branch else "All Branches",
        branch_count=branch_count,
        metrics=_role_metrics(role, academy, branch, branch_count),
        focus_items=ROLE_UI[role]["focus_items"],
        quick_actions=ROLE_UI[role]["quick_actions"],
        status_badge=ROLE_UI[role]["status_badge"],
        workflow_title=ROLE_UI[role]["workflow_title"],
        workflow_items=ROLE_UI[role]["workflow_items"],
        state_title=ROLE_UI[role]["state_title"],
        state_items=ROLE_UI[role]["state_items"],
    )


def _role_metrics(
    role: Role,
    academy: Academy | None,
    branch: Branch | None,
    branch_count: int,
) -> list[dict[str, str]]:
    academy_name = academy.name if academy else "Platform Scope"
    branch_name = branch.name if branch else "All Branches"
    values = {
        "academy_name": academy_name,
        "branch_name": branch_name,
        "branch_count": str(branch_count),
    }
    metrics = []
    for metric in ROLE_UI[role]["metrics"]:
        metrics.append(
            {
                "label": metric["label"],
                "value": metric["value"].format(**values),
                "tone": metric["tone"],
            }
        )
    return metrics
