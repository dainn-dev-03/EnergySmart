from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InvalidInputError
from app.models import Room
from app.repositories.floor_repository import FloorRepository
from app.repositories.meter_repository import MeterRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.common import Page
from app.schemas.room import RoomCreate, RoomListParams, RoomUpdate
from app.services.base_crud_service import CrudService


class RoomService(CrudService[Room, RoomCreate, RoomUpdate]):
    entity_label = "phòng"

    def __init__(self, db: Session) -> None:
        self.rooms = RoomRepository(db)
        self.floors = FloorRepository(db)
        self.meters = MeterRepository(db)
        super().__init__(db, self.rooms)

    def list(self, params: RoomListParams) -> Page[Room]:
        return self.rooms.list(params)

    def _prepare_values(
        self, data: RoomCreate | RoomUpdate, current: Room | None
    ) -> dict[str, Any]:
        if self.floors.get(data.floor_id) is None:
            raise InvalidInputError.for_field("floor_id", "Tầng không tồn tại")
        if self.rooms.code_exists(data.code, exclude_id=current.id if current else None):
            raise ConflictError.for_field("code", f"Mã phòng '{data.code}' đã tồn tại")
        return data.model_dump()

    def _ensure_can_delete(self, entity: Room) -> None:
        meter_count = self.meters.count_by_room(entity.id)
        if meter_count:
            raise ConflictError(f"Không thể xóa phòng đang có {meter_count} công tơ")
