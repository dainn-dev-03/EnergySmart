from sqlalchemy.orm import joinedload

from app.models import Floor, Room
from app.repositories.base import BaseRepository
from app.repositories.scopes import room_scope
from app.schemas.common import Page
from app.schemas.room import RoomListParams


class RoomRepository(BaseRepository[Room]):
    model = Room
    load_options = (joinedload(Room.floor).joinedload(Floor.building),)
    search_columns = (Room.name, Room.code)
    sort_columns = {
        "code": Room.code,
        "name": Room.name,
        "area": Room.area,
        "created_at": Room.created_at,
    }

    def list(self, params: RoomListParams) -> Page[Room]:
        filters = room_scope(floor_id=params.floor_id, building_id=params.building_id)
        return self._list(params, filters)

    def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        return self._exists(Room.code == code, exclude_id=exclude_id)

    def count_by_floor(self, floor_id: int) -> int:
        return self._count(Room.floor_id == floor_id)
