from sqlalchemy import select

from app.models import Building
from app.repositories.base import BaseRepository
from app.schemas.building import BuildingListParams
from app.schemas.common import Page


class BuildingRepository(BaseRepository[Building]):
    model = Building
    search_columns = (Building.name, Building.code, Building.address)
    sort_columns = {"code": Building.code, "name": Building.name, "created_at": Building.created_at}

    def list(self, params: BuildingListParams) -> Page[Building]:
        return self._list(params)

    def get_by_code(self, code: str) -> Building | None:
        return self.db.scalar(select(Building).where(Building.code == code))

    def code_exists(self, code: str, exclude_id: int | None = None) -> bool:
        return self._exists(Building.code == code, exclude_id=exclude_id)
