from datetime import datetime

from sqlalchemy.orm import joinedload

from app.core.timezone import local_day_end_exclusive, local_day_start
from app.models import ElectricityUsage, Floor, Meter, Room
from app.repositories.base import BaseRepository
from app.repositories.scopes import meter_id_scope
from app.schemas.common import Page
from app.schemas.electricity_usage import ElectricityUsageListParams


class ElectricityUsageRepository(BaseRepository[ElectricityUsage]):
    model = ElectricityUsage
    load_options = (
        joinedload(ElectricityUsage.meter)
        .joinedload(Meter.room)
        .joinedload(Room.floor)
        .joinedload(Floor.building),
    )
    sort_columns = {
        "recorded_at": ElectricityUsage.recorded_at,
        "kwh": ElectricityUsage.kwh,
        "cost": ElectricityUsage.cost,
    }

    def list(self, params: ElectricityUsageListParams) -> Page[ElectricityUsage]:
        filters = meter_id_scope(
            ElectricityUsage.meter_id,
            meter_id=params.meter_id,
            room_id=params.room_id,
            floor_id=params.floor_id,
            building_id=params.building_id,
        )
        if params.from_date is not None:
            filters.append(ElectricityUsage.recorded_at >= local_day_start(params.from_date))
        if params.to_date is not None:
            filters.append(ElectricityUsage.recorded_at < local_day_end_exclusive(params.to_date))
        return self._list(params, filters)

    def reading_exists(
        self, meter_id: int, recorded_at: datetime, exclude_id: int | None = None
    ) -> bool:
        return self._exists(
            ElectricityUsage.meter_id == meter_id,
            ElectricityUsage.recorded_at == recorded_at,
            exclude_id=exclude_id,
        )
