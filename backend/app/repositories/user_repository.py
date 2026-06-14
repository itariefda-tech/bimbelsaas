from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_active_by_id(self, user_id: UUID) -> User | None:
        return db.session.scalar(
            select(User)
            .options(
                selectinload(User.role_assignments),
                selectinload(User.academy),
            )
            .where(User.id == user_id, User.status == "active")
        )

    def get_for_login(self, email: str, academy_id: UUID | None) -> User | None:
        return db.session.scalar(
            select(User)
            .options(
                selectinload(User.role_assignments),
                selectinload(User.academy),
            )
            .where(
                User.academy_id == academy_id,
                User.email == email,
                User.status == "active",
            )
        )

    def get_by_email(self, email: str, academy_id: UUID | None) -> User | None:
        return db.session.scalar(
            select(User).where(
                User.academy_id == academy_id,
                User.email == email,
            )
        )
