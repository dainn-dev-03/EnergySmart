"""Reusable column mixins and column-type helpers for ORM models."""

from datetime import datetime
from enum import StrEnum

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.user import User

# Keep timestamp columns at the end of every table.
_TIMESTAMP_SORT_ORDER = 100


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), sort_order=_TIMESTAMP_SORT_ORDER
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), sort_order=_TIMESTAMP_SORT_ORDER + 1
    )


class ActorMixin:
    """Attribution columns shared by mutable business entities."""

    @declared_attr
    def created_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def updated_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def created_by(cls) -> Mapped["User | None"]:
        return relationship("User", foreign_keys=[cls.created_by_id])

    @declared_attr
    def updated_by(cls) -> Mapped["User | None"]:
        return relationship("User", foreign_keys=[cls.updated_by_id])


def str_enum(enum_class: type[StrEnum], name: str, length: int = 20) -> Enum:
    """VARCHAR column with a CHECK constraint (no native PG enum, easier to migrate)."""
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
