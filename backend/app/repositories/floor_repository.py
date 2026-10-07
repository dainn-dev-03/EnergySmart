from sqlalchemy import ColumnElement
from sqlalchemy.orm import joinedload

from app.models import Floor
from app.repositories.base import BaseRepository
from app.schemas.common import Page
from app.schemas.floor import FloorListParams


class FloorRepository(BaseRepository[Floor]):
    model = Floor
    load_options = (joinedload(Floor.building),)
    search_columns = (Floor.name,)
    sort_columns = {
        "floor_number": Floor.floor_number,
        "name": Floor.name,
        "created_at": Floor.created_at,
    }

    def list(self, params: FloorListParams) -> Page[Floor]:
        filters: list[ColumnElement[bool]] = []
        if params.building_id is not None:
            filters.append(Floor.building_id == params.building_id)
        return self._list(params, filters)

    def floor_number_exists(
        self, building_id: int, floor_number: int, exclude_id: int | None = None
    ) -> bool:
        return self._exists(
            Floor.building_id == building_id,
            Floor.floor_number == floor_number,
            exclude_id=exclude_id,
        )

    def count_by_building(self, building_id: int) -> int:
        return self._count(Floor.building_id == building_id)
