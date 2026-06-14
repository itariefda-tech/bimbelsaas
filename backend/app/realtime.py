from flask_socketio import disconnect, join_room

from app.extensions import socketio
from app.permissions.constants import ScopeType
from app.services.auth_service import AuthService


def register_realtime_handlers() -> None:
    @socketio.on("connect")
    def connect(auth):
        token = auth.get("token") if isinstance(auth, dict) else None
        if not token:
            return False
        try:
            principal = AuthService().authenticate_access_token(token)
        except Exception:
            return False
        join_room(f"user:{principal.user.id}")
        if principal.user.academy_id:
            join_room(f"academy:{principal.user.academy_id}")
        for assignment in principal.assignments:
            if assignment.branch_id:
                join_room(f"branch:{assignment.branch_id}")
            if (
                assignment.scope_type == ScopeType.ASSIGNED_CLASS
                and assignment.scope_id
            ):
                join_room(f"class:{assignment.scope_id}")
            if (
                assignment.scope_type == ScopeType.LINKED_STUDENT
                and assignment.scope_id
            ):
                join_room(f"student:{assignment.scope_id}")
        return True

    @socketio.on("disconnect_request")
    def disconnect_request():
        disconnect()
