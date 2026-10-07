from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, InvalidInputError
from app.core.timezone import local_date
from app.models import ElectricityUsage
from app.repositories.electricity_price_repository import ElectricityPriceRepository
from app.repositories.electricity_usage_repository import ElectricityUsageRepository
from app.repositories.meter_repository import MeterRepository
from app.schemas.common import Page
from app.schemas.electricity_usage import (
    ElectricityUsageCreate,
    ElectricityUsageListParams,
    ElectricityUsageUpdate,
)
from app.services.base_crud_service import CrudService

_VND = Decimal("0.01")


def calculate_cost(kwh: Decimal, price_per_kwh: Decimal) -> Decimal:
    return (kwh * price_per_kwh).quantize(_VND, rounding=ROUND_HALF_UP)


class ElectricityUsageService(
    CrudService[ElectricityUsage, ElectricityUsageCreate, ElectricityUsageUpdate]
):
    """`cost` is derived from the price valid on the reading's local date, never from input."""

    entity_label = "dữ liệu điện năng"

    def __init__(self, db: Session) -> None:
        self.usages = ElectricityUsageRepository(db)
        self.meters = MeterRepository(db)
        self.prices = ElectricityPriceRepository(db)
        super().__init__(db, self.usages)

    def list(self, params: ElectricityUsageListParams) -> Page[ElectricityUsage]:
        return self.usages.list(params)

    def _prepare_values(
        self,
        data: ElectricityUsageCreate | ElectricityUsageUpdate,
        current: ElectricityUsage | None,
    ) -> dict[str, Any]:
        if self.meters.get(data.meter_id) is None:
            raise InvalidInputError.for_field("meter_id", "Công tơ không tồn tại")
        if self.usages.reading_exists(
            data.meter_id, data.recorded_at, exclude_id=current.id if current else None
        ):
            raise ConflictError.for_field("recorded_at", "Công tơ đã có dữ liệu tại thời điểm này")
        return {**data.model_dump(), "cost": self._cost_at(data.kwh, data.recorded_at)}

    def _cost_at(self, kwh: Decimal, recorded_at: datetime) -> Decimal:
        day = local_date(recorded_at)
        price = self.prices.find_active_on(day)
        if price is None:
            raise BusinessRuleError(
                f"Chưa có bảng giá điện áp dụng cho ngày {day.isoformat()}",
                code="PRICE_NOT_FOUND",
            )
        return calculate_cost(kwh, price.price_per_kwh)
