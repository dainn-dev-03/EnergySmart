"""Generic CRUD use cases. Subclasses plug in validation through the `_prepare_values` and
`_ensure_can_delete` hooks; the service owns the transaction (commit) boundary."""

from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError
from app.repositories.base import BaseRepository


class CrudService[ModelT: Base, CreateT: BaseModel, UpdateT: BaseModel]:
    # Vietnamese noun used in messages, e.g. "tòa nhà".
    entity_label: str

    def __init__(self, db: Session, repository: BaseRepository[ModelT]) -> None:
        self.db = db
        self.repository = repository

    def get(self, entity_id: int) -> ModelT:
        entity = self.repository.get(entity_id)
        if entity is None:
            raise NotFoundError(f"Không tìm thấy {self.entity_label} có id={entity_id}")
        return entity

    def create(self, data: CreateT) -> ModelT:
        values = self._prepare_values(data, current=None)
        entity = self.repository.add(self.repository.model(**values))
        return self._commit(entity)

    def update(self, entity_id: int, data: UpdateT) -> ModelT:
        entity = self.get(entity_id)
        values = self._prepare_values(data, current=entity)
        for field, value in values.items():
            setattr(entity, field, value)
        self.db.flush()
        return self._commit(entity)

    def delete(self, entity_id: int) -> None:
        entity = self.get(entity_id)
        self._ensure_can_delete(entity)
        self.repository.delete(entity)
        self.db.commit()

    def _prepare_values(self, data: CreateT | UpdateT, current: ModelT | None) -> dict[str, Any]:
        """Validate input against the database and return column values to persist.

        `current` is None on create and the entity being edited on update.
        """
        return data.model_dump()

    def _ensure_can_delete(self, entity: ModelT) -> None:
        """Raise ConflictError when the entity is still referenced."""

    def _commit(self, entity: ModelT) -> ModelT:
        self.db.commit()
        # Reload server-side values (updated_at) and relationships changed through FK columns.
        self.db.refresh(entity)
        return entity
