"""Demo building layout: 1 building, 10 floors, 50 rooms, 50 meters, and the price table."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from functools import cache

from sqlalchemy.orm import Session

from app.core.enums import MeterStatus, MeterType
from app.models import Building, ElectricityPrice, Floor, Meter, Room
from app.seed.usage_simulator import (
    CANTEEN,
    HVAC,
    LOBBY,
    MEETING,
    OFFICE,
    PANTRY,
    SECURITY,
    SERVER,
    STORAGE,
    LoadProfile,
    MeterLoad,
)

BUILDING_CODE = "ES-01"
# Whole-building consumption of a normal weekday (all ACTIVE meters), before seasonal effects.
TARGET_WEEKDAY_KWH = 1250.0
INACTIVE_METERS = frozenset({"M024", "M045"})
# Kept off floor 3, whose demo event (+25% in the last week) must stay clearly visible.
MAINTENANCE_METERS = frozenset({"M020", "M038"})
OLD_PRICE = Decimal("2500.00")
CURRENT_PRICE = Decimal("2650.00")


@dataclass(frozen=True)
class RoomSpec:
    name: str
    profile: LoadProfile
    weight: float  # relative peak load, calibrated to kW below
    area: Decimal
    three_phase: bool = False


@dataclass(frozen=True)
class FloorSpec:
    number: int
    name: str
    rooms: tuple[RoomSpec, ...]


@dataclass(frozen=True)
class MeterSpec:
    room_code: str
    room_name: str
    area: Decimal
    installation_date: date
    load: MeterLoad


def building_layout() -> list[FloorSpec]:
    office_rooms = (
        RoomSpec("Văn phòng mở A", OFFICE, 3.0, Decimal("150"), three_phase=True),
        RoomSpec("Văn phòng mở B", OFFICE, 2.4, Decimal("120")),
        RoomSpec("Phòng họp", MEETING, 1.4, Decimal("55")),
        RoomSpec("Phòng làm việc riêng", OFFICE, 0.9, Decimal("35")),
        RoomSpec("Pantry", PANTRY, 0.6, Decimal("20")),
    )
    floors = [
        FloorSpec(
            1,
            "Tầng 1 - Sảnh & dịch vụ",
            (
                RoomSpec("Sảnh chính", LOBBY, 2.0, Decimal("220"), three_phase=True),
                RoomSpec("Quầy lễ tân", OFFICE, 0.6, Decimal("30")),
                RoomSpec("Căng tin", CANTEEN, 2.5, Decimal("180"), three_phase=True),
                RoomSpec("Phòng bảo vệ", SECURITY, 0.5, Decimal("20")),
                RoomSpec("Kho tổng", STORAGE, 0.3, Decimal("60")),
            ),
        )
    ]
    floors += [FloorSpec(n, f"Tầng {n} - Văn phòng", office_rooms) for n in range(2, 10)]
    floors.append(
        FloorSpec(
            10,
            "Tầng 10 - Kỹ thuật",
            (
                RoomSpec("Phòng máy chủ", SERVER, 2.0, Decimal("60"), three_phase=True),
                RoomSpec("Phòng UPS", SERVER, 0.8, Decimal("25"), three_phase=True),
                RoomSpec("Phòng điều hòa trung tâm", HVAC, 4.0, Decimal("80"), three_phase=True),
                RoomSpec("Phòng kỹ thuật", OFFICE, 0.7, Decimal("30")),
                RoomSpec("Kho thiết bị", STORAGE, 0.3, Decimal("40")),
            ),
        )
    )
    return floors


def _meter_status(meter_code: str) -> MeterStatus:
    if meter_code in INACTIVE_METERS:
        return MeterStatus.INACTIVE
    if meter_code in MAINTENANCE_METERS:
        return MeterStatus.MAINTENANCE
    return MeterStatus.ACTIVE


@cache
def meter_specs() -> dict[str, MeterSpec]:
    """Meter specs keyed by meter code, with peak loads calibrated to TARGET_WEEKDAY_KWH."""
    raw: list[tuple[str, str, str, RoomSpec, int, MeterStatus, float]] = []
    for floor in building_layout():
        # Small per-floor variation so floors differ in the "by floor" charts.
        floor_weight = 0.9 + 0.05 * (floor.number % 4)
        for index, room in enumerate(floor.rooms, start=1):
            meter_code = f"M{len(raw) + 1:03d}"
            room_code = f"R{floor.number:02d}{index:02d}"
            status = _meter_status(meter_code)
            raw.append(
                (
                    meter_code,
                    room_code,
                    room.name,
                    room,
                    floor.number,
                    status,
                    room.weight * floor_weight,
                )
            )

    active_weekday_kwh_per_kw = sum(
        weight * room.profile.weekday_peak_hours
        for _, _, _, room, _, status, weight in raw
        if status is MeterStatus.ACTIVE
    )
    kw_per_weight = TARGET_WEEKDAY_KWH / active_weekday_kwh_per_kw

    specs: dict[str, MeterSpec] = {}
    for position, (
        meter_code,
        room_code,
        room_name,
        room,
        floor_number,
        status,
        weight,
    ) in enumerate(raw):
        specs[meter_code] = MeterSpec(
            room_code=room_code,
            room_name=room_name,
            area=room.area,
            installation_date=date(2023, 1, 9) + timedelta(days=7 * (position % 12)),
            load=MeterLoad(
                meter_code=meter_code,
                floor_number=floor_number,
                profile=room.profile,
                peak_kw=round(weight * kw_per_weight, 3),
                three_phase=room.three_phase,
                status=status,
            ),
        )
    return specs


def create_master_data(db: Session) -> list[Meter]:
    """Persist the building tree and return its meters (ordered by code)."""
    specs = meter_specs()
    building = Building(
        name="EnergySmart Tower",
        code=BUILDING_CODE,
        address="Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội",
        description="Tòa nhà văn phòng 10 tầng dùng cho demo hệ thống quản lý điện năng",
    )
    meters: list[Meter] = []
    for floor_spec in building_layout():
        floor = Floor(building=building, name=floor_spec.name, floor_number=floor_spec.number)
        for index, _ in enumerate(floor_spec.rooms, start=1):
            room_code = f"R{floor_spec.number:02d}{index:02d}"
            meter_code, spec = next(
                (code, spec) for code, spec in specs.items() if spec.room_code == room_code
            )
            room = Room(floor=floor, name=spec.room_name, code=room_code, area=spec.area)
            meters.append(
                Meter(
                    room=room,
                    meter_code=meter_code,
                    name=f"Công tơ {spec.room_name} (T{floor_spec.number})",
                    meter_type=MeterType.THREE_PHASE
                    if spec.load.three_phase
                    else MeterType.SINGLE_PHASE,
                    status=spec.load.status,
                    installation_date=spec.installation_date,
                )
            )
    db.add(building)
    db.flush()
    return meters


def create_prices(db: Session, today: date) -> list[ElectricityPrice]:
    """Two consecutive periods; the current price starts on the 1st of the previous month."""
    change_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    prices = [
        ElectricityPrice(
            name="Giá điện kinh doanh (cũ)",
            price_per_kwh=OLD_PRICE,
            effective_from=date(today.year - 1, 1, 1),
            effective_to=change_date - timedelta(days=1),
        ),
        ElectricityPrice(
            name="Giá điện kinh doanh (hiện hành)",
            price_per_kwh=CURRENT_PRICE,
            effective_from=change_date,
            effective_to=None,
        ),
    ]
    db.add_all(prices)
    db.flush()
    return prices


def seeded_meter_loads(meters: Sequence[Meter]) -> list[tuple[int, MeterLoad]]:
    """(meter_id, load) for meters of the demo layout; others are ignored.

    The status stored in the database wins, so a meter switched to INACTIVE through the API
    stops receiving simulated data.
    """
    specs = meter_specs()
    return [
        (meter.id, replace(specs[meter.meter_code].load, status=meter.status))
        for meter in meters
        if meter.meter_code in specs
    ]
