"""Reusable column mixins and column-type helpers for ORM models."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, func
from sqlalchemy.orm import Mapped, mapped_column

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
