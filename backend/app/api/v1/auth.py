from flask import Blueprint, g

from app.common.responses import success_response
from app.common.validation import json_payload, optional_uuid, required_string
from app.permissions.decorators import require_auth
from app.services.auth_service import AuthService

auth_api = Blueprint("auth", __name__, url_prefix="/auth")


@auth_api.post("/login")
def login():
    payload = json_payload()
    data = AuthService().login(
        email=required_string(payload, "email"),
        password=required_string(payload, "password"),
        academy_id=optional_uuid(payload.get("academy_id"), "academy_id"),
    )
    return success_response(data=data, message="Login successful.")


@auth_api.post("/refresh")
def refresh():
    payload = json_payload()
    data = AuthService().refresh(required_string(payload, "refresh_token"))
    return success_response(data=data, message="Session refreshed.")


@auth_api.post("/logout")
@require_auth
def logout():
    AuthService().logout(g.principal)
    return success_response(data=None, message="Logout successful.")


@auth_api.get("/me")
@require_auth
def current_user():
    principal = g.principal
    return success_response(
        message="Current user loaded.",
        data={
            "id": str(principal.user.id),
            "academy_id": (
                str(principal.user.academy_id)
                if principal.user.academy_id
                else None
            ),
            "email": principal.user.email,
            "full_name": principal.user.full_name,
            "roles": [
                {
                    "id": str(assignment.id),
                    "role": assignment.role,
                    "scope_type": assignment.scope_type,
                    "academy_id": (
                        str(assignment.academy_id)
                        if assignment.academy_id
                        else None
                    ),
                    "branch_id": (
                        str(assignment.branch_id)
                        if assignment.branch_id
                        else None
                    ),
                    "scope_id": (
                        str(assignment.scope_id)
                        if assignment.scope_id
                        else None
                    ),
                }
                for assignment in principal.assignments
            ],
        },
    )
