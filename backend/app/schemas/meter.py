from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import MeterStatus, MeterType
from app.schemas.common import Code, OrmModel, SearchableListParams, ShortName
from app.schemas.room import RoomRef


class MeterCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "room_id": 1,
                    "meter_code": "M001",
                    "name": "Công tơ phòng họp lớn",
                    "meter_type": "SINGLE_PHASE",
                    "status": "ACTIVE",
                    "installation_date": "2025-01-15",
                }
            ]
        }
    )

    room_id: int = Field(gt=0)
    meter_code: Code
    name: ShortName
    meter_type: MeterType
    status: MeterStatus = MeterStatus.ACTIVE
    installation_date: date | None = None

    @field_validator("installation_date")
    @classmethod
    def _not_in_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Ngày lắp đặt không được ở tương lai")
        return value


class MeterUpdate(MeterCreate):
    pass


class MeterRef(OrmModel):
    id: int
    meter_code: str
    name: str
    room: RoomRef


class MeterRead(OrmModel):
    id: int
    room_id: int
    meter_code: str
    name: str
    meter_type: MeterType
    status: MeterStatus
    installation_date: date | None
    created_at: datetime
    updated_at: datetime
    room: RoomRef


class MeterListParams(SearchableListParams):
    room_id: int | None = None
    floor_id: int | None = None
    building_id: int | None = None
    status: MeterStatus | None = None
    meter_type: MeterType | None = None
    sort_by: Literal["meter_code", "name", "status", "installation_date", "created_at"] = (
        "meter_code"
    )
