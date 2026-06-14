from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.room import Room
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self) -> None:
        super().__init__(Room)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        room_id: UUID,
    ) -> Room | None:
        return db.session.scalar(
            select(Room).where(
                Room.id == room_id,
                Room.academy_id == academy_id,
                Room.branch_id == branch_id,
            )
        )

    def get_by_code(
        self,
        academy_id: UUID,
        branch_id: UUID,
        room_code: str,
    ) -> Room | None:
        return db.session.scalar(
            select(Room).where(
                Room.academy_id == academy_id,
                Room.branch_id == branch_id,
                Room.room_code == room_code,
            )
        )

    def list_for_branch(self, academy_id: UUID, branch_id: UUID) -> list[Room]:
        return list(
            db.session.scalars(
                select(Room)
                .where(
                    Room.academy_id == academy_id,
                    Room.branch_id == branch_id,
                    Room.status != "archived",
                )
                .order_by(Room.room_name)
            )
        )
