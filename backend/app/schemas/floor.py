from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.building import BuildingRef
from app.schemas.common import OptionalText, OrmModel, SearchableListParams, ShortName


class FloorCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"building_id": 1, "name": "Tầng 3", "floor_number": 3, "description": None}
            ]
        }
    )

    building_id: int = Field(gt=0)
    name: ShortName
    floor_number: int = Field(ge=-10, le=200, description="Số tầng (tầng hầm là số âm)")
    description: OptionalText = None


class FloorUpdate(FloorCreate):
    pass


class FloorRef(OrmModel):
    id: int
    name: str
    floor_number: int
    building: BuildingRef


class FloorRead(OrmModel):
    id: int
    building_id: int
    name: str
    floor_number: int
    description: str | None
    created_at: datetime
    updated_at: datetime
    building: BuildingRef


class FloorListParams(SearchableListParams):
    building_id: int | None = None
    sort_by: Literal["floor_number", "name", "created_at"] = "floor_number"
