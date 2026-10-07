from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import DecimalNumber, OrmModel, SearchableListParams, ShortName, SortOrder


class ElectricityPriceCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Giá kinh doanh 2026",
                    "price_per_kwh": 2100,
                    "effective_from": "2026-01-01",
                    "effective_to": None,
                }
            ]
        }
    )

    name: ShortName
    price_per_kwh: Decimal = Field(gt=0, max_digits=10, decimal_places=2, description="VND/kWh")
    effective_from: date
    effective_to: date | None = Field(None, description="Bỏ trống nếu đang áp dụng")

    @model_validator(mode="after")
    def _valid_range(self) -> Self:
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu hiệu lực")
        return self


class ElectricityPriceUpdate(ElectricityPriceCreate):
    pass


class ElectricityPriceRead(OrmModel):
    id: int
    name: str
    price_per_kwh: DecimalNumber
    effective_from: date
    effective_to: date | None
    created_at: datetime


class ElectricityPriceListParams(SearchableListParams):
    active_on: date | None = Field(None, description="Chỉ lấy bảng giá có hiệu lực vào ngày này")
    sort_by: Literal["effective_from", "price_per_kwh", "name"] = "effective_from"
    sort_order: SortOrder = SortOrder.DESC
