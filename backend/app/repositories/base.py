from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

from app.extensions import db

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def add(self, entity: ModelType) -> ModelType:
        db.session.add(entity)
        return entity

    def get_by_id(self, entity_id: UUID) -> ModelType | None:
        return db.session.scalar(select(self.model).where(self.model.id == entity_id))

