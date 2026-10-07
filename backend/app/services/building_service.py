from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models import Building
from app.repositories.building_repository import BuildingRepository
from app.repositories.floor_repository import FloorRepository
from app.schemas.building import BuildingCreate, BuildingListParams, BuildingUpdate
from app.schemas.common import Page
from app.services.base_crud_service import CrudService


class BuildingService(CrudService[Building, BuildingCreate, BuildingUpdate]):
    entity_label = "tòa nhà"

    def __init__(self, db: Session) -> None:
        self.buildings = BuildingRepository(db)
        self.floors = FloorRepository(db)
        super().__init__(db, self.buildings)

    def list(self, params: BuildingListParams) -> Page[Building]:
        return self.buildings.list(params)

    def _prepare_values(
        self, data: BuildingCreate | BuildingUpdate, current: Building | None
    ) -> dict[str, Any]:
        if self.buildings.code_exists(data.code, exclude_id=current.id if current else None):
            raise ConflictError.for_field("code", f"Mã tòa nhà '{data.code}' đã tồn tại")
        return data.model_dump()

    def _ensure_can_delete(self, entity: Building) -> None:
        floor_count = self.floors.count_by_building(entity.id)
        if floor_count:
            raise ConflictError(f"Không thể xóa tòa nhà đang có {floor_count} tầng")
