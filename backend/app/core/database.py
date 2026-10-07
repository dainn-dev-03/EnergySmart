"""SQLAlchemy engine, session factory and declarative base."""

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Deterministic constraint names so Alembic migrations stay stable across databases.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {datetime: DateTime(timezone=True)}


# Every connection runs in UTC so returned timestamps never depend on the server TimeZone
# setting; conversion to local business time is done explicitly (app.core.timezone).
CONNECT_ARGS: dict[str, Any] = {
    "connect_timeout": settings.database_connect_timeout_seconds,
    "options": "-c timezone=UTC",
}

engine = create_engine(settings.database_uri, pool_pre_ping=True, connect_args=CONNECT_ARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
