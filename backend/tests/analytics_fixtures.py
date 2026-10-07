"""Small, hand-computable dataset for dashboard and analytics tests."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.timezone import APP_TIMEZONE
from app.models import Building, Floor, Meter
from tests.factories import create_building, create_floor, create_meter, create_room, create_usage

# Wednesday, 10:30 in Vietnam.
NOW = datetime(2025, 6, 4, 10, 30, tzinfo=APP_TIMEZONE)


def local(day: int, hour: int, month: int = 6) -> datetime:
    return datetime(2025, month, day, hour, tzinfo=APP_TIMEZONE)


@dataclass(frozen=True)
class TwoFloors:
    building: Building
    floor_1: Floor
    floor_2: Floor
    meter_a: Meter  # floor 1, room R0101
    meter_b: Meter  # floor 2, room R0201


def build_two_floors(db: Session) -> TwoFloors:
    building = create_building(db, code="ES-01")
    floor_1 = create_floor(db, building, floor_number=1)
    floor_2 = create_floor(db, building, floor_number=2)
    meter_a = create_meter(db, create_room(db, floor_1, code="R0101", name="Phòng A"), "MA")
    meter_b = create_meter(db, create_room(db, floor_2, code="R0201", name="Phòng B"), "MB")
    return TwoFloors(building, floor_1, floor_2, meter_a, meter_b)


def add_usage(db: Session, meter: Meter, at: datetime, kwh: str) -> None:
    create_usage(db, meter, recorded_at=at, kwh=Decimal(kwh))
