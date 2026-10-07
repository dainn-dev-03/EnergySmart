from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import (
    Code,
    DecimalNumber,
    OptionalText,
    OrmModel,
    SearchableListParams,
    ShortName,
)
from app.schemas.floor import FloorRef


class RoomCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "floor_id": 1,
                    "name": "Phòng họp lớn",
                    "code": "R0301",
                    "area": 65.5,
                    "description": None,
                }
            ]
        }
    )

    floor_id: int = Field(gt=0)
    name: ShortName
    code: Code
    area: Decimal | None = Field(
        None, gt=0, max_digits=10, decimal_places=2, description="Diện tích (m²)"
    )
    description: OptionalText = None


class RoomUpdate(RoomCreate):
    pass


class RoomRef(OrmModel):
    id: int
    name: str
    code: str
    floor: FloorRef


class RoomRead(OrmModel):
    id: int
    floor_id: int
    name: str
    code: str
    area: DecimalNumber | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    floor: FloorRef


class RoomListParams(SearchableListParams):
    floor_id: int | None = None
    building_id: int | None = None
    sort_by: Literal["code", "name", "area", "created_at"] = "code"
