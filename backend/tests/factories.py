"""Minimal builders for test data, shared across test modules."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.enums import MeterStatus, MeterType, UserRole
from app.core.security import create_access_token, hash_password
from app.models import (
    Building,
    ElectricityPrice,
    ElectricityUsage,
    Floor,
    Meter,
    Room,
    User,
)

DEFAULT_PASSWORD = "Secret#123"


def create_user(
    session: Session,
    username: str = "admin",
    role: UserRole = UserRole.ADMIN,
    password: str = DEFAULT_PASSWORD,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        email=f"{username}@energysmart.vn",
        full_name=f"User {username}",
        role=role,
        is_active=is_active,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.flush()
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.role).token
    return {"Authorization": f"Bearer {token}"}


def create_building(session: Session, code: str = "B01", name: str = "Tòa nhà A") -> Building:
    building = Building(name=name, code=code, address="Hà Nội")
    session.add(building)
    session.flush()
    return building


def create_floor(
    session: Session, building: Building | None = None, floor_number: int = 1
) -> Floor:
    floor = Floor(
        building=building or create_building(session),
        name=f"Tầng {floor_number}",
        floor_number=floor_number,
    )
    session.add(floor)
    session.flush()
    return floor


def create_room(
    session: Session, floor: Floor | None = None, code: str = "R0101", name: str = "Phòng 101"
) -> Room:
    room = Room(floor=floor or create_floor(session), name=name, code=code, area=Decimal("45.50"))
    session.add(room)
    session.flush()
    return room


def create_meter(
    session: Session,
    room: Room | None = None,
    meter_code: str = "M001",
    status: MeterStatus = MeterStatus.ACTIVE,
) -> Meter:
    meter = Meter(
        room=room or create_room(session),
        meter_code=meter_code,
        name=f"Công tơ {meter_code}",
        meter_type=MeterType.SINGLE_PHASE,
        status=status,
    )
    session.add(meter)
    session.flush()
    return meter


def create_price(
    session: Session,
    price_per_kwh: Decimal = Decimal("2500.00"),
    effective_from: date = date(2020, 1, 1),
    effective_to: date | None = None,
    name: str = "Giá kinh doanh",
) -> ElectricityPrice:
    price = ElectricityPrice(
        name=name,
        price_per_kwh=price_per_kwh,
        effective_from=effective_from,
        effective_to=effective_to,
    )
    session.add(price)
    session.flush()
    return price


def create_usage(
    session: Session,
    meter: Meter,
    recorded_at: datetime | None = None,
    kwh: Decimal = Decimal("1.250"),
) -> ElectricityUsage:
    usage = ElectricityUsage(
        meter_id=meter.id,
        recorded_at=recorded_at or datetime(2025, 6, 1, 1, tzinfo=UTC),
        kwh=kwh,
        cost=kwh * Decimal("2500"),
    )
    session.add(usage)
    session.flush()
    return usage
