from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.common import (
    Code,
    LongName,
    OptionalAddress,
    OptionalText,
    OrmModel,
    SearchableListParams,
)


class BuildingCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "EnergySmart Tower",
                    "code": "ES-01",
                    "address": "1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội",
                    "description": "Tòa nhà văn phòng 10 tầng",
                }
            ]
        }
    )

    name: LongName
    code: Code
    address: OptionalAddress = None
    description: OptionalText = None


class BuildingUpdate(BuildingCreate):
    pass


class BuildingRef(OrmModel):
    id: int
    name: str
    code: str


class BuildingRead(OrmModel):
    id: int
    name: str
    code: str
    address: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class BuildingListParams(SearchableListParams):
    sort_by: Literal["code", "name", "created_at"] = "code"
