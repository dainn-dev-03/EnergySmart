from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models import ElectricityPrice
from app.repositories.electricity_price_repository import ElectricityPriceRepository
from app.schemas.common import Page
from app.schemas.electricity_price import (
    ElectricityPriceCreate,
    ElectricityPriceListParams,
    ElectricityPriceUpdate,
)
from app.services.base_crud_service import CrudService


class ElectricityPriceService(
    CrudService[ElectricityPrice, ElectricityPriceCreate, ElectricityPriceUpdate]
):
    """Price periods must not overlap, so every day maps to at most one price."""

    entity_label = "bảng giá điện"

    def __init__(self, db: Session) -> None:
        self.prices = ElectricityPriceRepository(db)
        super().__init__(db, self.prices)

    def list(self, params: ElectricityPriceListParams) -> Page[ElectricityPrice]:
        return self.prices.list(params)

    def _prepare_values(
        self,
        data: ElectricityPriceCreate | ElectricityPriceUpdate,
        current: ElectricityPrice | None,
    ) -> dict[str, Any]:
        overlapping = self.prices.find_overlapping(
            data.effective_from, data.effective_to, exclude_id=current.id if current else None
        )
        if overlapping is not None:
            period_end = overlapping.effective_to.isoformat() if overlapping.effective_to else "nay"
            raise ConflictError.for_field(
                "effective_from",
                f"Khoảng hiệu lực trùng với bảng giá '{overlapping.name}' "
                f"({overlapping.effective_from.isoformat()} → {period_end})",
            )
        return data.model_dump()
