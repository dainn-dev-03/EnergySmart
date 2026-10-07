from collections.abc import Sequence
from datetime import date

from sqlalchemy import ColumnElement, or_, select

from app.models import ElectricityPrice
from app.repositories.base import BaseRepository
from app.schemas.common import Page
from app.schemas.electricity_price import ElectricityPriceListParams


def _active_on(day: date) -> ColumnElement[bool]:
    return (ElectricityPrice.effective_from <= day) & or_(
        ElectricityPrice.effective_to.is_(None), ElectricityPrice.effective_to >= day
    )


class ElectricityPriceRepository(BaseRepository[ElectricityPrice]):
    model = ElectricityPrice
    search_columns = (ElectricityPrice.name,)
    sort_columns = {
        "effective_from": ElectricityPrice.effective_from,
        "price_per_kwh": ElectricityPrice.price_per_kwh,
        "name": ElectricityPrice.name,
    }

    def list(self, params: ElectricityPriceListParams) -> Page[ElectricityPrice]:
        filters = [_active_on(params.active_on)] if params.active_on is not None else []
        return self._list(params, filters)

    def list_all(self) -> Sequence[ElectricityPrice]:
        statement = select(ElectricityPrice).order_by(ElectricityPrice.effective_from)
        return self.db.scalars(statement).all()

    def find_active_on(self, day: date) -> ElectricityPrice | None:
        statement = (
            select(ElectricityPrice)
            .where(_active_on(day))
            .order_by(ElectricityPrice.effective_from.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def find_overlapping(
        self, effective_from: date, effective_to: date | None, exclude_id: int | None = None
    ) -> ElectricityPrice | None:
        """First price period intersecting [effective_from, effective_to] (None = open-ended)."""
        conditions: list[ColumnElement[bool]] = [
            or_(
                ElectricityPrice.effective_to.is_(None),
                ElectricityPrice.effective_to >= effective_from,
            )
        ]
        if effective_to is not None:
            conditions.append(ElectricityPrice.effective_from <= effective_to)
        if exclude_id is not None:
            conditions.append(ElectricityPrice.id != exclude_id)
        statement = (
            select(ElectricityPrice)
            .where(*conditions)
            .order_by(ElectricityPrice.effective_from)
            .limit(1)
        )
        return self.db.scalar(statement)
