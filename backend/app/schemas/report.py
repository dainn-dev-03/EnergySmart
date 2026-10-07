from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.analytics import DateRangeParams
from app.schemas.common import DecimalNumber

ReportGroup = Literal["floor", "room", "meter"]


class ConsumptionReportParams(DateRangeParams):
    group_by: ReportGroup = Field("floor", description="Gom nhóm theo tầng, phòng hoặc công tơ")


class ReportRow(BaseModel):
    code: str
    name: str
    parent: str = Field(description="Tầng chứa phòng/công tơ (để trống khi gom theo tầng)")
    kwh: DecimalNumber
    cost: DecimalNumber
    share_percent: float


class ConsumptionReport(BaseModel):
    from_date: date
    to_date: date
    group_by: ReportGroup
    total_kwh: DecimalNumber
    total_cost: DecimalNumber
    rows: list[ReportRow]
