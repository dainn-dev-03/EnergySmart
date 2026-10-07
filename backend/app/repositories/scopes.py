"""Reusable WHERE conditions that scope rows by the Building → Floor → Room → Meter hierarchy.

Implemented as `IN (subquery)` so they compose with any statement without extra joins.
"""

from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import InstrumentedAttribute

from app.models import Floor, Meter, Room


def room_scope(
    *, floor_id: int | None = None, building_id: int | None = None
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if floor_id is not None:
        conditions.append(Room.floor_id == floor_id)
    if building_id is not None:
        conditions.append(
            Room.floor_id.in_(select(Floor.id).where(Floor.building_id == building_id))
        )
    return conditions


def meter_scope(
    *, room_id: int | None = None, floor_id: int | None = None, building_id: int | None = None
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if room_id is not None:
        conditions.append(Meter.room_id == room_id)
    if floor_id is not None or building_id is not None:
        rooms = select(Room.id).where(*room_scope(floor_id=floor_id, building_id=building_id))
        conditions.append(Meter.room_id.in_(rooms))
    return conditions


def meter_id_scope(
    meter_id_column: InstrumentedAttribute[Any],
    *,
    meter_id: int | None = None,
    room_id: int | None = None,
    floor_id: int | None = None,
    building_id: int | None = None,
) -> list[ColumnElement[bool]]:
    """Scope a table that references meters (usages, alerts) through its `meter_id` column."""
    conditions: list[ColumnElement[bool]] = []
    if meter_id is not None:
        conditions.append(meter_id_column == meter_id)
    if room_id is not None or floor_id is not None or building_id is not None:
        meters = select(Meter.id).where(
            *meter_scope(room_id=room_id, floor_id=floor_id, building_id=building_id)
        )
        conditions.append(meter_id_column.in_(meters))
    return conditions
