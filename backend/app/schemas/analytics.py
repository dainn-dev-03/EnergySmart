from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import DecimalNumber

MAX_RANGE_DAYS = 731


class ScopeParams(BaseModel):
    """Optional Building → Floor → Room → Meter filter shared by analytics endpoints."""

    building_id: int | None = None
    floor_id: int | None = None
    room_id: int | None = None
    meter_id: int | None = None


class DateRangeParams(ScopeParams):
    from_date: date | None = Field(
        None, description="Từ ngày (giờ Việt Nam). Mặc định tùy endpoint"
    )
    to_date: date | None = Field(None, description="Đến ngày, bao gồm (mặc định hôm nay)")

    @model_validator(mode="after")
    def _valid_range(self) -> Self:
        if self.from_date and self.to_date:
            if self.from_date > self.to_date:
                raise ValueError("from_date phải trước hoặc bằng to_date")
            if (self.to_date - self.from_date).days >= MAX_RANGE_DAYS:
                raise ValueError(f"Khoảng thời gian tối đa {MAX_RANGE_DAYS} ngày")
        return self


class RoomBreakdownParams(DateRangeParams):
    limit: int | None = Field(None, ge=1, le=200, description="Chỉ lấy N phòng tiêu thụ nhiều nhất")


class ComparisonParams(ScopeParams):
    period: Literal["day", "week", "month"] = Field(
        "month", description="Kỳ so sánh khi không truyền current_from/current_to"
    )
    reference_date: date | None = Field(
        None, description="Ngày thuộc kỳ hiện tại (mặc định hôm nay)"
    )
    current_from: date | None = Field(None, description="Kỳ tùy chọn: từ ngày")
    current_to: date | None = Field(None, description="Kỳ tùy chọn: đến ngày (bao gồm)")

    @model_validator(mode="after")
    def _valid_custom_range(self) -> Self:
        if (self.current_from is None) != (self.current_to is None):
            raise ValueError("Cần truyền đủ cả current_from và current_to")
        if self.current_from and self.current_to and self.current_from > self.current_to:
            raise ValueError("current_from phải trước hoặc bằng current_to")
        return self


class DailyPoint(BaseModel):
    date: date
    kwh: DecimalNumber
    cost: DecimalNumber


class MonthlyPoint(BaseModel):
    month: str = Field(description="YYYY-MM")
    kwh: DecimalNumber
    cost: DecimalNumber


class HourlyPoint(BaseModel):
    hour: int
    weekday_kwh: DecimalNumber = Field(description="kWh trung bình mỗi ngày thường tại giờ này")
    weekend_kwh: DecimalNumber = Field(description="kWh trung bình mỗi ngày cuối tuần tại giờ này")


class FloorConsumption(BaseModel):
    floor_id: int
    floor_number: int
    floor_name: str
    kwh: DecimalNumber
    cost: DecimalNumber
    share_percent: float


class RoomConsumption(BaseModel):
    room_id: int
    room_code: str
    room_name: str
    floor_name: str
    kwh: DecimalNumber
    cost: DecimalNumber
    share_percent: float


class PeriodTotal(BaseModel):
    start: datetime
    end: datetime
    kwh: DecimalNumber
    cost: DecimalNumber


class Comparison(BaseModel):
    period: Literal["day", "week", "month", "custom"]
    current_period: PeriodTotal
    previous_period: PeriodTotal
    difference: DecimalNumber = Field(description="kWh kỳ này - kỳ trước")
    percentage_change: float | None = Field(description="null khi kỳ trước bằng 0")
    cost_difference: DecimalNumber
    cost_percentage_change: float | None
