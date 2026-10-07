"""Create or top up the demo building and its simulated hourly electricity readings."""

from bisect import bisect_right
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.core.timezone import APP_TIMEZONE, local_day_start
from app.models import Alert, Building, ElectricityPrice, ElectricityUsage, Floor, Meter, Room
from app.repositories.alert_repository import AlertRepository
from app.repositories.building_repository import BuildingRepository
from app.repositories.electricity_price_repository import ElectricityPriceRepository
from app.repositories.electricity_usage_repository import ElectricityUsageRepository
from app.repositories.meter_repository import MeterRepository
from app.seed.master_data import (
    BUILDING_CODE,
    create_master_data,
    create_prices,
    meter_specs,
    seeded_meter_loads,
)
from app.seed.usage_simulator import DemoScenario, UsageSimulator
from app.services.alert_service import AlertService

# Children first; users are never touched by a reset.
_DEMO_TABLES = (Alert, ElectricityUsage, Meter, Room, Floor, Building, ElectricityPrice)


# On a fresh seed, alerts older than this are marked resolved so only recent ones stay open.
OPEN_ALERT_DAYS = 3


@dataclass(frozen=True)
class SeedReport:
    created_master_data: bool
    meter_count: int
    inserted_readings: int
    last_reading_at: datetime
    created_alerts: int
    open_alerts: int


class PriceBook:
    """In-memory price lookup by local date (avoids one query per generated reading)."""

    def __init__(self, prices: Sequence[ElectricityPrice]) -> None:
        self._periods = sorted(prices, key=lambda price: price.effective_from)
        self._starts = [price.effective_from for price in self._periods]

    def price_on(self, day: date) -> Decimal:
        index = bisect_right(self._starts, day) - 1
        if index >= 0:
            period = self._periods[index]
            if period.effective_to is None or day <= period.effective_to:
                return period.price_per_kwh
        raise BusinessRuleError(
            f"Chưa có bảng giá điện áp dụng cho ngày {day.isoformat()}", code="PRICE_NOT_FOUND"
        )


def reset_demo_data(db: Session) -> None:
    """Delete every building/meter/usage/alert/price row and restart their id sequences."""
    tables = ", ".join(model.__tablename__ for model in _DEMO_TABLES)
    db.execute(text(f"TRUNCATE {tables} RESTART IDENTITY"))


def last_complete_hour(now: datetime) -> datetime:
    """Start of the most recent finished hour, in local time."""
    local_now = now.astimezone(APP_TIMEZONE)
    return local_now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


def seed_demo_data(
    db: Session, *, days: int, random_seed: int, now: datetime | None = None
) -> SeedReport:
    """First run: build the demo tree with `days` of history. Later runs: fill the gap to now."""
    end = last_complete_hour(now or datetime.now(APP_TIMEZONE))
    today = end.date()
    meters_repository = MeterRepository(db)
    usages = ElectricityUsageRepository(db)

    created = BuildingRepository(db).get_by_code(BUILDING_CODE) is None
    meters: Sequence[Meter]
    if created:
        meters = create_master_data(db)
        create_prices(db, today)
    else:
        meters = meters_repository.list_by_codes(meter_specs().keys())

    loads = seeded_meter_loads(meters)
    history_start = local_day_start(today - timedelta(days=days - 1))
    latest = (
        {} if created else usages.latest_recorded_at_by_meter([meter_id for meter_id, _ in loads])
    )
    simulator = UsageSimulator(DemoScenario(today=today), random_seed)
    price_book = PriceBook(ElectricityPriceRepository(db).list_all())

    rows: list[dict[str, Any]] = []
    for meter_id, load in loads:
        previous = latest.get(meter_id)
        start = previous + timedelta(hours=1) if previous is not None else history_start
        rows.extend(simulator.rows(meter_id, load, start, end, price_book.price_on))
    inserted = usages.bulk_insert(rows)

    # Detect alerts on every complete day that just received data.
    detect_from = (
        history_start.date()
        if created
        else min(
            (latest_at.astimezone(APP_TIMEZONE).date() for latest_at in latest.values()),
            default=today,
        )
    )
    yesterday = today - timedelta(days=1)
    alerts = AlertRepository(db)
    created_alerts = 0
    if detect_from <= yesterday:
        detection = AlertService(db, now=lambda: end).detect_range(detect_from, yesterday)
        created_alerts = detection.created_alerts
    if created:
        alerts.resolve_before(today - timedelta(days=OPEN_ALERT_DAYS))

    return SeedReport(
        created_master_data=created,
        meter_count=len(loads),
        inserted_readings=inserted,
        last_reading_at=end,
        created_alerts=created_alerts,
        open_alerts=alerts.count_unresolved(),
    )
