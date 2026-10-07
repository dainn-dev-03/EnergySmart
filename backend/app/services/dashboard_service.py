"""Dashboard widgets: fixed time windows built on top of AnalyticsService."""

from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.enums import MeterStatus
from app.core.timezone import add_months, local_day_start, local_now, month_start
from app.repositories.alert_repository import AlertRepository
from app.repositories.analytics_repository import ZERO, AnalyticsRepository, UsageScope
from app.repositories.meter_repository import MeterRepository
from app.schemas.analytics import DailyPoint, MonthlyPoint, RoomConsumption
from app.schemas.dashboard import DashboardSummary, FloorTrend
from app.services.analytics_service import AnalyticsService, percentage_change

# A floor whose last-7-days consumption grew by at least this much is flagged.
FLOOR_INCREASE_WARNING_PERCENT = 20.0
TREND_WINDOW = timedelta(days=7)


class DashboardService:
    def __init__(self, db: Session, now: Callable[[], datetime] = local_now) -> None:
        self.analytics_service = AnalyticsService(db, now)
        self.analytics = AnalyticsRepository(db)
        self.meters = MeterRepository(db)
        self.alerts = AlertRepository(db)
        self._now = now

    def summary(self, building_id: int | None) -> DashboardSummary:
        now = self._now()
        scope = UsageScope(building_id=building_id)
        today = self.analytics.totals(local_day_start(now.date()), now, scope)
        month = self.analytics.totals(local_day_start(month_start(now.date())), now, scope)
        return DashboardSummary(
            today_kwh=today.kwh,
            month_kwh=month.kwh,
            month_cost=month.cost,
            active_meters=self.meters.count_by_status(MeterStatus.ACTIVE, building_id),
            alert_count=self.alerts.count_unresolved(building_id),
        )

    def daily(self, days: int, building_id: int | None) -> list[DailyPoint]:
        today = self._now().date()
        return self.analytics_service.daily_series(
            today - timedelta(days=days - 1), today, UsageScope(building_id=building_id)
        )

    def monthly(self, months: int, building_id: int | None) -> list[MonthlyPoint]:
        today = self._now().date()
        return self.analytics_service.monthly_series(
            add_months(today, -(months - 1)), today, UsageScope(building_id=building_id)
        )

    def floor_trends(self, building_id: int | None) -> list[FloorTrend]:
        now = self._now()
        scope = UsageScope(building_id=building_id)
        current = self.analytics.by_floor(now - TREND_WINDOW, now, scope)
        previous = {
            row.floor_id: row.kwh
            for row in self.analytics.by_floor(now - 2 * TREND_WINDOW, now - TREND_WINDOW, scope)
        }
        trends = []
        for row in current:
            previous_kwh = previous.get(row.floor_id, ZERO)
            change = percentage_change(row.kwh, previous_kwh)
            warning = change is not None and change >= FLOOR_INCREASE_WARNING_PERCENT
            trends.append(
                FloorTrend(
                    floor_id=row.floor_id,
                    floor_number=row.floor_number,
                    floor_name=row.floor_name,
                    kwh=row.kwh,
                    previous_kwh=previous_kwh,
                    percentage_change=change,
                    status="WARNING" if warning else "NORMAL",
                )
            )
        return trends

    def top_rooms(self, limit: int, building_id: int | None) -> list[RoomConsumption]:
        """Rooms consuming the most since the start of the current month."""
        today = self._now().date()
        return self.analytics_service.room_breakdown(
            month_start(today), today, UsageScope(building_id=building_id), limit
        )
