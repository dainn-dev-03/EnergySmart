from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.timezone import ensure_aware
from app.schemas.common import DecimalNumber, ListParams, OrmModel, SortOrder
from app.schemas.meter import MeterRef


class ElectricityUsageCreate(BaseModel):
    """One hourly reading: `kwh` consumed during the hour starting at `recorded_at`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "meter_id": 1,
                    "recorded_at": "2026-10-01T08:00:00+07:00",
                    "kwh": 1.25,
                    "voltage": 220.5,
                    "current": 6.12,
                    "power_factor": 0.93,
                }
            ]
        }
    )

    meter_id: int = Field(gt=0)
    recorded_at: datetime = Field(
        description="Đầu khung giờ đo (ISO 8601). Không có múi giờ thì hiểu là giờ Việt Nam."
    )
    kwh: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    voltage: Decimal | None = Field(None, ge=0, max_digits=6, decimal_places=2)
    current: Decimal | None = Field(None, ge=0, max_digits=8, decimal_places=3)
    power_factor: Decimal | None = Field(None, ge=0, le=1, max_digits=4, decimal_places=3)

    @field_validator("recorded_at")
    @classmethod
    def _valid_hour_start(cls, value: datetime) -> datetime:
        value = ensure_aware(value)
        if value.minute or value.second or value.microsecond:
            raise ValueError("Thời điểm ghi phải là đầu giờ (phút và giây bằng 0)")
        if value > datetime.now(UTC):
            raise ValueError("Không thể ghi nhận dữ liệu ở thời điểm tương lai")
        return value


class ElectricityUsageUpdate(ElectricityUsageCreate):
    pass


class ElectricityUsageRead(OrmModel):
    id: int
    meter_id: int
    recorded_at: datetime
    kwh: DecimalNumber
    voltage: DecimalNumber | None
    current: DecimalNumber | None
    power_factor: DecimalNumber | None
    cost: DecimalNumber
    created_at: datetime
    meter: MeterRef


class ElectricityUsageListParams(ListParams):
    meter_id: int | None = None
    room_id: int | None = None
    floor_id: int | None = None
    building_id: int | None = None
    from_date: date | None = Field(None, description="Từ ngày (giờ Việt Nam, bao gồm)")
    to_date: date | None = Field(None, description="Đến ngày (giờ Việt Nam, bao gồm)")
    sort_by: Literal["recorded_at", "kwh", "cost"] = "recorded_at"
    sort_order: SortOrder = SortOrder.DESC

    @model_validator(mode="after")
    def _valid_date_range(self) -> Self:
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date phải trước hoặc bằng to_date")
        return self
