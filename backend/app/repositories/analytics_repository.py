"""Aggregate queries over electricity usages, grouped in local business time (APP_TIMEZONE)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import ColumnElement, Date, Integer, cast, distinct, extract, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ElectricityUsage, Floor, Meter, Room
from app.repositories.scopes import meter_id_scope

ZERO = Decimal(0)

# recorded_at converted to a local wall-clock timestamp (no time zone) for grouping.
_LOCAL_TIME = func.timezone(settings.app_timezone, ElectricityUsage.recorded_at)
_KWH = func.coalesce(func.sum(ElectricityUsage.kwh), ZERO)
_COST = func.coalesce(func.sum(ElectricityUsage.cost), ZERO)


@dataclass(frozen=True)
class UsageScope:
    """Restricts aggregates to part of the Building → Floor → Room → Meter tree."""

    building_id: int | None = None
    floor_id: int | None = None
    room_id: int | None = None
    meter_id: int | None = None

    def conditions(self) -> list[ColumnElement[bool]]:
        return meter_id_scope(
            ElectricityUsage.meter_id,
            meter_id=self.meter_id,
            room_id=self.room_id,
            floor_id=self.floor_id,
            building_id=self.building_id,
        )


@dataclass(frozen=True)
class Totals:
    kwh: Decimal
    cost: Decimal


@dataclass(frozen=True)
class BucketTotals:
    bucket: date
    kwh: Decimal
    cost: Decimal


@dataclass(frozen=True)
class HourTotals:
    hour: int
    is_weekend: bool
    kwh: Decimal
    day_count: int


@dataclass(frozen=True)
class FloorTotals:
    floor_id: int
    floor_number: int
    floor_name: str
    kwh: Decimal
    cost: Decimal


@dataclass(frozen=True)
class RoomTotals:
    room_id: int
    room_code: str
    room_name: str
    floor_name: str
    kwh: Decimal
    cost: Decimal


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def totals(self, start: datetime, end: datetime, scope: UsageScope) -> Totals:
        statement = select(_KWH, _COST).where(*self._filters(start, end, scope))
        kwh, cost = self.db.execute(statement).one()
        return Totals(kwh=kwh, cost=cost)

    def series(
        self, unit: Literal["day", "month"], start: datetime, end: datetime, scope: UsageScope
    ) -> list[BucketTotals]:
        bucket = func.date_trunc(unit, _LOCAL_TIME)
        statement = (
            select(cast(bucket, Date), _KWH, _COST)
            .where(*self._filters(start, end, scope))
            .group_by(bucket)
            .order_by(bucket)
        )
        return [BucketTotals(day, kwh, cost) for day, kwh, cost in self.db.execute(statement)]

    def hourly(self, start: datetime, end: datetime, scope: UsageScope) -> list[HourTotals]:
        hour = cast(extract("hour", _LOCAL_TIME), Integer)
        is_weekend = extract("isodow", _LOCAL_TIME) >= 6
        statement = (
            select(hour, is_weekend, _KWH, func.count(distinct(cast(_LOCAL_TIME, Date))))
            .where(*self._filters(start, end, scope))
            .group_by(hour, is_weekend)
            .order_by(hour)
        )
        return [HourTotals(*row) for row in self.db.execute(statement)]

    def by_floor(self, start: datetime, end: datetime, scope: UsageScope) -> list[FloorTotals]:
        statement = (
            select(Floor.id, Floor.floor_number, Floor.name, _KWH, _COST)
            .select_from(ElectricityUsage)
            .join(Meter, Meter.id == ElectricityUsage.meter_id)
            .join(Room, Room.id == Meter.room_id)
            .join(Floor, Floor.id == Room.floor_id)
            .where(*self._filters(start, end, scope))
            .group_by(Floor.id)
            .order_by(Floor.floor_number)
        )
        return [FloorTotals(*row) for row in self.db.execute(statement)]

    def by_room(
        self, start: datetime, end: datetime, scope: UsageScope, limit: int | None = None
    ) -> list[RoomTotals]:
        statement = (
            select(Room.id, Room.code, Room.name, Floor.name, _KWH, _COST)
            .select_from(ElectricityUsage)
            .join(Meter, Meter.id == ElectricityUsage.meter_id)
            .join(Room, Room.id == Meter.room_id)
            .join(Floor, Floor.id == Room.floor_id)
            .where(*self._filters(start, end, scope))
            .group_by(Room.id, Floor.name)
            .order_by(_KWH.desc(), Room.code)
            .limit(limit)
        )
        return [RoomTotals(*row) for row in self.db.execute(statement)]

    @staticmethod
    def _filters(start: datetime, end: datetime, scope: UsageScope) -> Sequence[Any]:
        return [
            ElectricityUsage.recorded_at >= start,
            ElectricityUsage.recorded_at < end,
            *scope.conditions(),
        ]
