from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.auth_session import AuthSession
from app.models.user import User
from app.repositories.base import BaseRepository


class AuthSessionRepository(BaseRepository[AuthSession]):
    def __init__(self) -> None:
        super().__init__(AuthSession)

    def get_with_user(self, session_id: UUID) -> AuthSession | None:
        return db.session.scalar(
            select(AuthSession)
            .options(
                selectinload(AuthSession.user).selectinload(User.role_assignments),
                selectinload(AuthSession.user).selectinload(User.academy),
            )
            .where(AuthSession.id == session_id)
        )
