"""Generic CRUD use cases. Subclasses plug in validation through the `_prepare_values` and
`_ensure_can_delete` hooks; the service owns the transaction (commit) boundary."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError
from app.models import AuditLog, User
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

    def create(self, data: CreateT, actor: User) -> ModelT:
        values = self._prepare_values(data, current=None)
        values["created_by_id"] = actor.id
        values["updated_by_id"] = actor.id
        entity = self.repository.add(self.repository.model(**values))
        self._write_audit(actor, "CREATE", entity, self._changes(None, entity))
        return self._commit(entity)

    def update(self, entity_id: int, data: UpdateT, actor: User) -> ModelT:
        entity = self.get(entity_id)
        values = self._prepare_values(data, current=entity)
        changes = {field: [self._json_value(getattr(entity, field)), self._json_value(value)] for field, value in values.items() if getattr(entity, field) != value}
        for field, value in values.items():
            setattr(entity, field, value)
        if changes:
            entity.updated_by_id = actor.id
        self.db.flush()
        if changes:
            self._write_audit(actor, "UPDATE", entity, changes)
        return self._commit(entity)

    def delete(self, entity_id: int, actor: User) -> None:
        entity = self.get(entity_id)
        self._ensure_can_delete(entity)
        self._write_audit(actor, "DELETE", entity, self._changes(entity, None))
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

    def _write_audit(self, actor: User, action: str, entity: ModelT, changes: dict[str, list[Any]]) -> None:
        self.db.add(AuditLog(user_id=actor.id, action=action, entity_type=entity.__tablename__, entity_id=entity.id, entity_label=self._entity_label(entity), changes=changes or None))

    def _entity_label(self, entity: ModelT) -> str:
        for field in ("name", "code", "meter_code"):
            if value := getattr(entity, field, None):
                return str(value)
        return f"{self.entity_label} #{entity.id}"

    def _changes(self, before: ModelT | None, after: ModelT | None) -> dict[str, list[Any]]:
        entity = after or before
        assert entity is not None
        return {column.key: [self._json_value(getattr(before, column.key)) if before else None, self._json_value(getattr(after, column.key)) if after else None] for column in entity.__table__.columns if column.key not in {"id", "created_at", "updated_at", "created_by_id", "updated_by_id"}}

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, Enum): return value.value
        if isinstance(value, (datetime, date)): return value.isoformat()
        if isinstance(value, Decimal): return str(value)
        return value
