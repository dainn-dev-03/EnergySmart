from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InvalidInputError
from app.models import Floor
from app.repositories.building_repository import BuildingRepository
from app.repositories.floor_repository import FloorRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.common import Page
from app.schemas.floor import FloorCreate, FloorListParams, FloorUpdate
from app.services.base_crud_service import CrudService


class FloorService(CrudService[Floor, FloorCreate, FloorUpdate]):
    entity_label = "tầng"

    def __init__(self, db: Session) -> None:
        self.floors = FloorRepository(db)
        self.buildings = BuildingRepository(db)
        self.rooms = RoomRepository(db)
        super().__init__(db, self.floors)

    def list(self, params: FloorListParams) -> Page[Floor]:
        return self.floors.list(params)

    def _prepare_values(
        self, data: FloorCreate | FloorUpdate, current: Floor | None
    ) -> dict[str, Any]:
        if self.buildings.get(data.building_id) is None:
            raise InvalidInputError.for_field("building_id", "Tòa nhà không tồn tại")
        if self.floors.floor_number_exists(
            data.building_id, data.floor_number, exclude_id=current.id if current else None
        ):
            raise ConflictError.for_field(
                "floor_number", f"Tầng số {data.floor_number} đã tồn tại trong tòa nhà này"
            )
        return data.model_dump()

    def _ensure_can_delete(self, entity: Floor) -> None:
        room_count = self.rooms.count_by_floor(entity.id)
        if room_count:
            raise ConflictError(f"Không thể xóa tầng đang có {room_count} phòng")
