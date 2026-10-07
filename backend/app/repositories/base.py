"""Generic repository: the only layer that builds SQLAlchemy queries."""

from collections.abc import Sequence
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.orm.interfaces import ORMOption

from app.core.database import Base
from app.schemas.common import ListParams, Page, SearchableListParams, SortOrder


def contains_pattern(term: str) -> str:
    """ILIKE pattern matching `term` anywhere, with LIKE wildcards in the term escaped."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class BaseRepository[ModelT: Base]:
    model: type[ModelT]
    # Eager loads applied to every read (e.g. parent chain used by the read schema).
    load_options: ClassVar[Sequence[ORMOption]] = ()
    # Columns matched by the `search` list parameter.
    search_columns: ClassVar[Sequence[InstrumentedAttribute[Any]]] = ()
    # Allowed `sort_by` values mapped to columns.
    sort_columns: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {}

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id, options=self.load_options)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()

    def _exists(self, *conditions: ColumnElement[bool], exclude_id: int | None = None) -> bool:
        """True if a row matches; `exclude_id` skips the row being edited."""
        if exclude_id is not None:
            primary_key = self.model.__mapper__.primary_key[0]
            conditions = (*conditions, primary_key != exclude_id)
        return bool(self.db.scalar(select(select(self.model).where(*conditions).exists())))

    def _count(self, *conditions: ColumnElement[bool]) -> int:
        statement = select(func.count()).select_from(self.model).where(*conditions)
        return self.db.scalar(statement) or 0

    def _list(
        self, params: ListParams, filters: Sequence[ColumnElement[bool]] = ()
    ) -> Page[ModelT]:
        statement = select(self.model).options(*self.load_options).where(*filters)

        if isinstance(params, SearchableListParams) and params.search and self.search_columns:
            pattern = contains_pattern(params.search.strip())
            statement = statement.where(
                or_(*(column.ilike(pattern, escape="\\") for column in self.search_columns))
            )

        sort_column = self.sort_columns[params.sort_by]
        primary_key = self.model.__mapper__.primary_key[0]
        if params.sort_order is SortOrder.DESC:
            statement = statement.order_by(sort_column.desc().nulls_last(), primary_key.desc())
        else:
            statement = statement.order_by(sort_column.asc().nulls_last(), primary_key.asc())
        return self._paginate(statement, params.page, params.page_size)

    def _paginate(self, statement: Select[ModelT], page: int, page_size: int) -> Page[ModelT]:
        total = self.db.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        items = self.db.scalars(statement.limit(page_size).offset((page - 1) * page_size)).all()
        return Page(items=list(items), total=total or 0, page=page, page_size=page_size)
