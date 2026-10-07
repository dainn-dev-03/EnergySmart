from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, InvalidInputError
from app.models import Meter
from app.repositories.meter_repository import MeterRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.common import Page
from app.schemas.meter import MeterCreate, MeterListParams, MeterUpdate
from app.services.base_crud_service import CrudService


class MeterService(CrudService[Meter, MeterCreate, MeterUpdate]):
    """Deleting a meter also deletes its usages and alerts (ON DELETE CASCADE)."""

    entity_label = "công tơ"

    def __init__(self, db: Session) -> None:
        self.meters = MeterRepository(db)
        self.rooms = RoomRepository(db)
        super().__init__(db, self.meters)

    def list(self, params: MeterListParams) -> Page[Meter]:
        return self.meters.list(params)

    def _prepare_values(
        self, data: MeterCreate | MeterUpdate, current: Meter | None
    ) -> dict[str, Any]:
        if self.rooms.get(data.room_id) is None:
            raise InvalidInputError.for_field("room_id", "Phòng không tồn tại")
        if self.meters.code_exists(data.meter_code, exclude_id=current.id if current else None):
            raise ConflictError.for_field(
                "meter_code", f"Mã công tơ '{data.meter_code}' đã tồn tại"
            )
        return data.model_dump()
