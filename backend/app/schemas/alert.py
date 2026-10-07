from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from app.core.enums import AlertSeverity, AlertType
from app.schemas.common import DecimalNumber, ListParams, OrmModel, SortOrder
from app.schemas.meter import MeterRef


class AlertRead(OrmModel):
    id: int
    meter_id: int
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    threshold_value: DecimalNumber | None = Field(description="Ngưỡng kWh/ngày (trung bình × 1,2)")
    actual_value: DecimalNumber | None = Field(description="kWh thực tế của ngày")
    usage_date: date
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime | None
    meter: MeterRef


class AlertListParams(ListParams):
    is_resolved: bool | None = None
    severity: AlertSeverity | None = None
    meter_id: int | None = None
    room_id: int | None = None
    floor_id: int | None = None
    building_id: int | None = None
    from_date: date | None = Field(None, description="Lọc theo ngày phát sinh (usage_date)")
    to_date: date | None = None
    sort_by: Literal["created_at", "usage_date", "actual_value"] = "created_at"
    sort_order: SortOrder = SortOrder.DESC

    @model_validator(mode="after")
    def _valid_range(self) -> Self:
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date phải trước hoặc bằng to_date")
        return self


class DetectionResult(BaseModel):
    from_date: date
    to_date: date
    evaluated_meters: int
    created_alerts: int
    by_severity: dict[AlertSeverity, int]
