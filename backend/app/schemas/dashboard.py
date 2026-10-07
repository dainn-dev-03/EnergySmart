from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import DecimalNumber


class DashboardSummary(BaseModel):
    today_kwh: DecimalNumber
    month_kwh: DecimalNumber
    month_cost: DecimalNumber
    active_meters: int
    alert_count: int = Field(description="Số cảnh báo chưa xử lý")


class FloorTrend(BaseModel):
    """7 ngày gần nhất so với 7 ngày trước đó."""

    floor_id: int
    floor_number: int
    floor_name: str
    kwh: DecimalNumber
    previous_kwh: DecimalNumber
    percentage_change: float | None
    status: Literal["NORMAL", "WARNING"]
