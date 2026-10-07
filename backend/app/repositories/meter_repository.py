from collections.abc import Collection, Sequence

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Floor, Meter, Room
from app.repositories.base import BaseRepository
from app.repositories.scopes import meter_scope
from app.schemas.common import Page
from app.schemas.meter import MeterListParams

METER_LOAD_OPTIONS = (joinedload(Meter.room).joinedload(Room.floor).joinedload(Floor.building),)


class MeterRepository(BaseRepository[Meter]):
    model = Meter
    load_options = METER_LOAD_OPTIONS
    search_columns = (Meter.meter_code, Meter.name)
    sort_columns = {
        "meter_code": Meter.meter_code,
        "name": Meter.name,
        "status": Meter.status,
        "installation_date": Meter.installation_date,
        "created_at": Meter.created_at,
    }

    def list(self, params: MeterListParams) -> Page[Meter]:
        filters = meter_scope(
            room_id=params.room_id, floor_id=params.floor_id, building_id=params.building_id
        )
        if params.status is not None:
            filters.append(Meter.status == params.status)
        if params.meter_type is not None:
            filters.append(Meter.meter_type == params.meter_type)
        return self._list(params, filters)

    def code_exists(self, meter_code: str, exclude_id: int | None = None) -> bool:
        return self._exists(Meter.meter_code == meter_code, exclude_id=exclude_id)

    def list_by_codes(self, meter_codes: Collection[str]) -> Sequence[Meter]:
        statement = (
            select(Meter).where(Meter.meter_code.in_(meter_codes)).order_by(Meter.meter_code)
        )
        return self.db.scalars(statement).all()

    def count_by_room(self, room_id: int) -> int:
        return self._count(Meter.room_id == room_id)
