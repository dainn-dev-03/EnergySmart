"""Consumption reports (JSON and CSV export) grouped by floor, room or meter."""

from io import BytesIO
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy.orm import Session

from app.core.timezone import local_day_end_exclusive, local_day_start, local_now, month_start
from app.repositories.analytics_repository import ZERO, AnalyticsRepository
from app.schemas.report import ConsumptionReport, ConsumptionReportParams, ReportRow
from app.services.analytics_service import scope_of, share_percent

EXCEL_HEADERS = ("Mã", "Tên", "Thuộc", "Điện năng (kWh)", "Chi phí (VND)", "Tỷ trọng (%)")
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

    def consumption_excel(self, params: ConsumptionReportParams) -> tuple[str, bytes]:
        """Return a formatted Excel workbook for the requested consumption report."""
        report = self.consumption(params)
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Báo cáo điện năng"
        worksheet.append(EXCEL_HEADERS)

        header_fill = PatternFill(fill_type="solid", fgColor="1565C0")
        header_font = Font(color="FFFFFF", bold=True)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        worksheet.row_dimensions[1].height = 26

        for row in report.rows:
            worksheet.append(
                (row.code, row.name, row.parent, row.kwh, row.cost, row.share_percent / 100)
            )

        total_row = worksheet.max_row + 1
        worksheet.append(("", "Tổng cộng", "", report.total_kwh, report.total_cost, 1))
        for cell in worksheet[total_row]:
            cell.font = Font(bold=True)

        grid_side = Side(style="thin", color="D9E1F2")
        grid_border = Border(left=grid_side, right=grid_side, top=grid_side, bottom=grid_side)
        for row_index in range(1, total_row + 1):
            for column_index in range(1, 7):
                worksheet.cell(row_index, column_index).border = grid_border
        total_top = Side(style="thin", color="1565C0")
        for cell in worksheet[total_row]:
            cell.border = Border(left=grid_side, right=grid_side, top=total_top, bottom=grid_side)

        for row_index in range(2, total_row + 1):
            for column_index in range(1, 7):
                worksheet.cell(row_index, column_index).alignment = Alignment(
                    horizontal="right" if column_index >= 4 else "left",
                    vertical="center",
                )
            worksheet.cell(row_index, 4).number_format = "#,##0.000"
            worksheet.cell(row_index, 5).number_format = "#,##0"
            worksheet.cell(row_index, 6).number_format = "0.0%"

        for column, width in {
            "A": 16,
            "B": 32,
            "C": 22,
            "D": 20,
            "E": 20,
            "F": 16,
        }.items():
            worksheet.column_dimensions[column].width = width
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = f"A1:F{total_row - 1}"

        buffer = BytesIO()
        workbook.save(buffer)
        filename = (
            f"bao-cao-dien-nang_{GROUP_LABELS[report.group_by]}_"
            f"{report.from_date:%Y%m%d}-{report.to_date:%Y%m%d}.xlsx"
        )
        return filename, buffer.getvalue()
