"""Consumption reports (JSON and CSV export) grouped by floor, room or meter."""

import csv
import io
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.timezone import local_day_end_exclusive, local_day_start, local_now, month_start
from app.repositories.analytics_repository import ZERO, AnalyticsRepository
from app.schemas.report import ConsumptionReport, ConsumptionReportParams, ReportRow
from app.services.analytics_service import scope_of, share_percent

CSV_HEADERS = ("Mã", "Tên", "Thuộc", "Điện năng (kWh)", "Chi phí (VND)", "Tỷ trọng (%)")
UTF8_BOM = "\ufeff"
GROUP_LABELS = {"floor": "tang", "room": "phong", "meter": "cong-to"}


class ReportService:
    def __init__(self, db: Session, now: Callable[[], datetime] = local_now) -> None:
        self.analytics = AnalyticsRepository(db)
        self._now = now

    def consumption(self, params: ConsumptionReportParams) -> ConsumptionReport:
        """Default period: from the 1st of the current month to today."""
        to_date = params.to_date or self._now().date()
        from_date = params.from_date or month_start(to_date)
        start = local_day_start(from_date)
        end = min(local_day_end_exclusive(to_date), self._now())
        scope = scope_of(params)

        rows: list[tuple[str, str, str, Decimal, Decimal]]
        if params.group_by == "floor":
            rows = [
                (str(r.floor_number), r.floor_name, "", r.kwh, r.cost)
                for r in self.analytics.by_floor(start, end, scope)
            ]
        elif params.group_by == "room":
            rows = [
                (r.room_code, r.room_name, r.floor_name, r.kwh, r.cost)
                for r in self.analytics.by_room(start, end, scope)
            ]
        else:
            rows = [
                (r.meter_code, r.meter_name, r.floor_name, r.kwh, r.cost)
                for r in self.analytics.by_meter(start, end, scope)
            ]

        total_kwh = sum((row[3] for row in rows), ZERO)
        total_cost = sum((row[4] for row in rows), ZERO)
        return ConsumptionReport(
            from_date=from_date,
            to_date=to_date,
            group_by=params.group_by,
            total_kwh=total_kwh,
            total_cost=total_cost,
            rows=[
                ReportRow(
                    code=code,
                    name=name,
                    parent=parent,
                    kwh=kwh,
                    cost=cost,
                    share_percent=share_percent(kwh, total_kwh),
                )
                for code, name, parent, kwh, cost in rows
            ],
        )

    def consumption_csv(self, params: ConsumptionReportParams) -> tuple[str, str]:
        """(filename, CSV text). The UTF-8 BOM lets Excel display Vietnamese correctly."""
        report = self.consumption(params)
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\r\n")
        writer.writerow(CSV_HEADERS)
        for row in report.rows:
            writer.writerow(
                (
                    row.code,
                    row.name,
                    row.parent,
                    f"{row.kwh:.3f}",
                    f"{row.cost:.0f}",
                    row.share_percent,
                )
            )
        writer.writerow(
            ("", "Tổng cộng", "", f"{report.total_kwh:.3f}", f"{report.total_cost:.0f}", 100)
        )
        filename = (
            f"bao-cao-dien-nang_{GROUP_LABELS[report.group_by]}_"
            f"{report.from_date:%Y%m%d}-{report.to_date:%Y%m%d}.csv"
        )
        return filename, UTF8_BOM + buffer.getvalue()
