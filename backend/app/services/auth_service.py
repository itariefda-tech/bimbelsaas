from datetime import datetime, timezone
from uuid import UUID, uuid4

from flask import current_app, g, request
from werkzeug.security import check_password_hash

from app.common.errors import AuthenticationError
from app.domain.organization_status import AcademyStatus
from app.extensions import db
from app.models.auth_session import AuthSession
from app.permissions.context import Principal
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.role_assignment_repository import RoleAssignmentRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.token_service import TokenService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= _utc_now()


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        session_repository: AuthSessionRepository | None = None,
        assignment_repository: RoleAssignmentRepository | None = None,
        audit_service: AuditLogService | None = None,
    ) -> None:
        self.users = user_repository or UserRepository()
        self.sessions = session_repository or AuthSessionRepository()
        self.assignments = assignment_repository or RoleAssignmentRepository()
        self.audit = audit_service or AuditLogService()

    def login(
        self,
        *,
        email: str,
        password: str,
        academy_id: UUID | None,
    ) -> dict[str, object]:
        normalized_email = email.strip().lower()
        user = self.users.get_for_login(normalized_email, academy_id)
        if user is None or not check_password_hash(user.password_hash, password):
            self.audit.record(
                AuditEvent(
                    academy_id=academy_id,
                    entity_type="authentication",
                    entity_id=normalized_email,
                    action_type="auth.login_failed",
                    new_data={"success": False},
                    reason="invalid_credentials",
                    ip_address=request.remote_addr,
                    request_id=g.request_id,
                ),
                commit=True,
            )
            raise AuthenticationError(
                "The email, academy, or password is incorrect.",
                "invalid_credentials",
            )

        session_id = uuid4()
        access_token = TokenService.create_access_token(
            user_id=user.id,
            session_id=session_id,
        )
        refresh_token, refresh_jti = TokenService.create_refresh_token(
            user_id=user.id,
            session_id=session_id,
        )
        session = AuthSession(
            id=session_id,
            user_id=user.id,
            refresh_jti_hash=TokenService.hash_jti(refresh_jti),
            expires_at=_utc_now() + current_app.config["JWT_REFRESH_TTL"],
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:500],
        )
        self.sessions.add(session)
        user.last_login_at = _utc_now()

        self.audit.record(
            AuditEvent(
                academy_id=user.academy_id,
                actor_user_id=user.id,
                entity_type="auth_session",
                entity_id=str(session.id),
                action_type="auth.login",
                new_data={"user_id": str(user.id)},
                ip_address=request.remote_addr,
                request_id=g.request_id,
            )
        )
        db.session.commit()
        return self._token_response(user, access_token, refresh_token)

    def refresh(self, refresh_token: str) -> dict[str, object]:
        payload = TokenService.decode(refresh_token, expected_type="refresh")
        session = self._valid_session(payload)
        if session.refresh_jti_hash != TokenService.hash_jti(payload["jti"]):
            session.revoked_at = _utc_now()
            db.session.commit()
            raise AuthenticationError(
                "The refresh token has already been rotated or revoked.",
                "refresh_token_reused",
            )

        access_token = TokenService.create_access_token(
            user_id=session.user_id,
            session_id=session.id,
        )
        new_refresh_token, refresh_jti = TokenService.create_refresh_token(
            user_id=session.user_id,
            session_id=session.id,
        )
        session.refresh_jti_hash = TokenService.hash_jti(refresh_jti)
        session.last_used_at = _utc_now()
        session.expires_at = _utc_now() + current_app.config["JWT_REFRESH_TTL"]
        self.audit.record(
            AuditEvent(
                academy_id=session.user.academy_id,
                actor_user_id=session.user_id,
                entity_type="auth_session",
                entity_id=str(session.id),
                action_type="auth.refresh",
                ip_address=request.remote_addr,
                request_id=g.request_id,
            )
        )
        db.session.commit()
        return self._token_response(
            session.user,
            access_token,
            new_refresh_token,
        )

    def authenticate_access_token(self, token: str) -> Principal:
        payload = TokenService.decode(token, expected_type="access")
        session = self._valid_session(payload)
        assignments = tuple(
            self.assignments.list_active_for_user(session.user_id)
        )
        return Principal(
            user=session.user,
            session=session,
            assignments=assignments,
        )

    def logout(self, principal: Principal) -> None:
        principal.session.revoked_at = _utc_now()
        self.audit.record(
            AuditEvent(
                academy_id=principal.user.academy_id,
                actor_user_id=principal.user.id,
                entity_type="auth_session",
                entity_id=str(principal.session.id),
                action_type="auth.logout",
                ip_address=request.remote_addr,
                request_id=g.request_id,
            )
        )
        db.session.commit()

    def _valid_session(self, payload: dict[str, object]) -> AuthSession:
        try:
            session_id = UUID(str(payload["sid"]))
            user_id = UUID(str(payload["sub"]))
        except (KeyError, ValueError) as error:
            raise AuthenticationError(
                "The token subject is invalid.",
                "invalid_token",
            ) from error

        session = self.sessions.get_with_user(session_id)
        if (
            session is None
            or session.user_id != user_id
            or session.revoked_at is not None
            or _is_expired(session.expires_at)
            or session.user.status != "active"
            or (
                session.user.academy is not None
                and session.user.academy.status == AcademyStatus.ARCHIVED
            )
        ):
            raise AuthenticationError(
                "The session is no longer active.",
                "session_inactive",
            )
        return session

    @staticmethod
    def _token_response(user, access_token: str, refresh_token: str):
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": {
                "id": str(user.id),
                "academy_id": str(user.academy_id) if user.academy_id else None,
                "email": user.email,
                "full_name": user.full_name,
            },
        }
