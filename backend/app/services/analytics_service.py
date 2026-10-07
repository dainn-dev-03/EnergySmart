"""Consumption analytics. All day/month boundaries are local business time (APP_TIMEZONE)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidInputError
from app.core.timezone import (
    add_months,
    local_day_end_exclusive,
    local_day_start,
    local_now,
    month_start,
)
from app.repositories.analytics_repository import ZERO, AnalyticsRepository, UsageScope
from app.schemas.analytics import (
    Comparison,
    ComparisonParams,
    DailyPoint,
    DateRangeParams,
    FloorConsumption,
    HourlyPoint,
    MonthlyPoint,
    PeriodTotal,
    RoomBreakdownParams,
    RoomConsumption,
    ScopeParams,
)

DEFAULT_DAILY_DAYS = 30
DEFAULT_MONTHS = 12


def percentage_change(current: Decimal, previous: Decimal) -> float | None:
    """(current - previous) / previous * 100, or None when there is no previous value."""
    if previous == 0:
        return None
    return round(float((current - previous) / previous * 100), 2)


def share_percent(part: Decimal, total: Decimal) -> float:
    return round(float(part / total * 100), 2) if total else 0.0


def scope_of(params: ScopeParams) -> UsageScope:
    return UsageScope(
        building_id=params.building_id,
        floor_id=params.floor_id,
        room_id=params.room_id,
        meter_id=params.meter_id,
    )


@dataclass(frozen=True)
class DayRange:
    first_day: date
    last_day: date


class AnalyticsService:
    def __init__(self, db: Session, now: Callable[[], datetime] = local_now) -> None:
        self.analytics = AnalyticsRepository(db)
        self._now = now

    @property
    def today(self) -> date:
        return self._now().date()

    # ----- endpoints -------------------------------------------------------------------------

    def daily(self, params: DateRangeParams) -> list[DailyPoint]:
        days = self._day_range(params, default_days=DEFAULT_DAILY_DAYS)
        return self.daily_series(days.first_day, days.last_day, scope_of(params))

    def monthly(self, params: DateRangeParams) -> list[MonthlyPoint]:
        last_day = params.to_date or self.today
        first_day = params.from_date or add_months(last_day, -(DEFAULT_MONTHS - 1))
        return self.monthly_series(month_start(first_day), last_day, scope_of(params))

    def hourly(self, params: DateRangeParams) -> list[HourlyPoint]:
        days = self._day_range(params, default_days=DEFAULT_DAILY_DAYS)
        start, end = self._bounds(days.first_day, days.last_day)
        weekday: dict[int, Decimal] = {}
        weekend: dict[int, Decimal] = {}
        for row in self.analytics.hourly(start, end, scope_of(params)):
            target = weekend if row.is_weekend else weekday
            target[row.hour] = row.kwh / row.day_count if row.day_count else ZERO
        return [
            HourlyPoint(
                hour=hour,
                weekday_kwh=round(weekday.get(hour, ZERO), 3),
                weekend_kwh=round(weekend.get(hour, ZERO), 3),
            )
            for hour in range(24)
        ]

    def by_floor(self, params: DateRangeParams) -> list[FloorConsumption]:
        days = self._day_range(params, default_days=DEFAULT_DAILY_DAYS)
        start, end = self._bounds(days.first_day, days.last_day)
        rows = self.analytics.by_floor(start, end, scope_of(params))
        total = sum((row.kwh for row in rows), ZERO)
        return [
            FloorConsumption(
                floor_id=row.floor_id,
                floor_number=row.floor_number,
                floor_name=row.floor_name,
                kwh=row.kwh,
                cost=row.cost,
                share_percent=share_percent(row.kwh, total),
            )
            for row in rows
        ]

    def by_room(self, params: RoomBreakdownParams) -> list[RoomConsumption]:
        days = self._day_range(params, default_days=DEFAULT_DAILY_DAYS)
        return self.room_breakdown(days.first_day, days.last_day, scope_of(params), params.limit)

    def comparison(self, params: ComparisonParams) -> Comparison:
        scope = scope_of(params)
        now = self._now()
        if params.current_from and params.current_to:
            period: Literal["day", "week", "month", "custom"] = "custom"
            current_start = local_day_start(params.current_from)
            period_end = local_day_end_exclusive(params.current_to)
            previous_start = current_start - (period_end - current_start)
        else:
            period = params.period
            reference = params.reference_date or now.date()
            current_start, period_end, previous_start = _period_bounds(period, reference)

        current_end = min(period_end, now)
        if current_end <= current_start:
            raise InvalidInputError.for_field("reference_date", "Kỳ so sánh chưa bắt đầu")
        # Compare the same elapsed time, never spilling into the current period.
        previous_end = min(previous_start + (current_end - current_start), current_start)

        current = self._period_total(current_start, current_end, scope)
        previous = self._period_total(previous_start, previous_end, scope)
        return Comparison(
            period=period,
            current_period=current,
            previous_period=previous,
            difference=current.kwh - previous.kwh,
            percentage_change=percentage_change(current.kwh, previous.kwh),
            cost_difference=current.cost - previous.cost,
            cost_percentage_change=percentage_change(current.cost, previous.cost),
        )

    # ----- building blocks shared with the dashboard -----------------------------------------

    def daily_series(self, first_day: date, last_day: date, scope: UsageScope) -> list[DailyPoint]:
        start, end = self._bounds(first_day, last_day)
        found = {row.bucket: row for row in self.analytics.series("day", start, end, scope)}
        points = []
        day = first_day
        while day <= last_day:
            row = found.get(day)
            points.append(
                DailyPoint(date=day, kwh=row.kwh if row else ZERO, cost=row.cost if row else ZERO)
            )
            day += timedelta(days=1)
        return points

    def monthly_series(
        self, first_month: date, last_day: date, scope: UsageScope
    ) -> list[MonthlyPoint]:
        start, end = self._bounds(first_month, last_day)
        found = {row.bucket: row for row in self.analytics.series("month", start, end, scope)}
        points = []
        month = first_month
        while month <= last_day:
            row = found.get(month)
            points.append(
                MonthlyPoint(
                    month=month.strftime("%Y-%m"),
                    kwh=row.kwh if row else ZERO,
                    cost=row.cost if row else ZERO,
                )
            )
            month = add_months(month, 1)
        return points

    def room_breakdown(
        self, first_day: date, last_day: date, scope: UsageScope, limit: int | None
    ) -> list[RoomConsumption]:
        start, end = self._bounds(first_day, last_day)
        total = self.analytics.totals(start, end, scope).kwh
        return [
            RoomConsumption(
                room_id=row.room_id,
                room_code=row.room_code,
                room_name=row.room_name,
                floor_name=row.floor_name,
                kwh=row.kwh,
                cost=row.cost,
                share_percent=share_percent(row.kwh, total),
            )
            for row in self.analytics.by_room(start, end, scope, limit)
        ]

    def _period_total(self, start: datetime, end: datetime, scope: UsageScope) -> PeriodTotal:
        totals = self.analytics.totals(start, end, scope)
        return PeriodTotal(start=start, end=end, kwh=totals.kwh, cost=totals.cost)

    def _day_range(self, params: DateRangeParams, default_days: int) -> DayRange:
        last_day = params.to_date or self.today
        first_day = params.from_date or last_day - timedelta(days=default_days - 1)
        return DayRange(first_day, last_day)

    def _bounds(self, first_day: date, last_day: date) -> tuple[datetime, datetime]:
        """[start of first_day, end of last_day), never beyond now."""
        return local_day_start(first_day), min(local_day_end_exclusive(last_day), self._now())


def _period_bounds(
    period: Literal["day", "week", "month"], reference: date
) -> tuple[datetime, datetime, datetime]:
    """(current_start, current_period_end, previous_start) of the period containing reference."""
    if period == "day":
        return (
            local_day_start(reference),
            local_day_end_exclusive(reference),
            local_day_start(reference - timedelta(days=1)),
        )
    if period == "week":
        monday = reference - timedelta(days=reference.weekday())
        return (
            local_day_start(monday),
            local_day_start(monday + timedelta(days=7)),
            local_day_start(monday - timedelta(days=7)),
        )
    first = month_start(reference)
    return (
        local_day_start(first),
        local_day_start(add_months(first, 1)),
        local_day_start(add_months(first, -1)),
    )
