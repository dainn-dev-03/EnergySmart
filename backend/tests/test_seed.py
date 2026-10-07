from datetime import datetime
from decimal import Decimal

from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.enums import UserRole
from app.core.security import verify_password
from app.core.timezone import APP_TIMEZONE
from app.models import Building, ElectricityPrice, ElectricityUsage, Floor, Meter, Room, User
from app.repositories.user_repository import UserRepository
from app.seed.demo_data import reset_demo_data, seed_demo_data
from app.seed.master_data import CURRENT_PRICE
from app.seed.settings import SeedSettings
from app.seed.users import seed_users

# Wednesday 2025-06-04 10:30 in Vietnam -> last complete hour is 09:00.
NOW = datetime(2025, 6, 4, 10, 30, tzinfo=APP_TIMEZONE)


def _seed_settings(demo_password: str | None = "demo123") -> SeedSettings:
    return SeedSettings(
        admin_username="admin",
        admin_password=SecretStr("admin123"),
        admin_email="admin@energysmart.vn",
        demo_password=SecretStr(demo_password) if demo_password else None,
    )


def test_seed_users_creates_admin_and_demo_accounts(db_session: Session) -> None:
    created = seed_users(db_session, _seed_settings())

    assert created == ["admin", "manager", "viewer"]
    admin = UserRepository(db_session).get_by_username("admin")
    assert admin is not None
    assert admin.role == UserRole.ADMIN
    assert verify_password("admin123", admin.password_hash)


def test_seed_users_is_idempotent(db_session: Session) -> None:
    seed_users(db_session, _seed_settings())

    created_again = seed_users(db_session, _seed_settings())

    assert created_again == []
    assert db_session.scalar(select(func.count()).select_from(User)) == 3


def test_seed_users_skips_demo_accounts_without_demo_password(db_session: Session) -> None:
    assert seed_users(db_session, _seed_settings(demo_password=None)) == ["admin"]


def _count(db: Session, model: type[Base]) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_seed_demo_data_creates_building_tree_and_readings(db_session: Session) -> None:
    report = seed_demo_data(db_session, days=3, random_seed=42, now=NOW)

    assert report.created_master_data
    assert report.last_reading_at == datetime(2025, 6, 4, 9, tzinfo=APP_TIMEZONE)
    counts = {
        model.__name__: _count(db_session, model)
        for model in (Building, Floor, Room, Meter, ElectricityPrice)
    }
    assert counts == {"Building": 1, "Floor": 10, "Room": 50, "Meter": 50, "ElectricityPrice": 2}
    # 46 active meters x (24 + 24 + 10 hours); 2 maintenance meters only report on 06-02;
    # 2 inactive meters stopped 30 days ago.
    assert report.inserted_readings == 46 * 58 + 2 * 24
    assert _count(db_session, ElectricityUsage) == report.inserted_readings


def test_seeded_cost_uses_price_of_the_day(db_session: Session) -> None:
    seed_demo_data(db_session, days=1, random_seed=42, now=NOW)

    usage = db_session.scalars(select(ElectricityUsage).limit(1)).one()

    assert usage.cost == (usage.kwh * CURRENT_PRICE).quantize(Decimal("0.01"))


def test_second_run_only_tops_up_missing_hours(db_session: Session) -> None:
    seed_demo_data(db_session, days=2, random_seed=42, now=NOW)

    unchanged = seed_demo_data(db_session, days=2, random_seed=42, now=NOW)
    three_hours_later = seed_demo_data(db_session, days=2, random_seed=42, now=NOW.replace(hour=13))

    assert not unchanged.created_master_data
    assert unchanged.inserted_readings == 0
    assert three_hours_later.inserted_readings == 46 * 3
    assert _count(db_session, Building) == 1


def test_reset_removes_demo_data_but_keeps_users(db_session: Session) -> None:
    seed_users(db_session, _seed_settings())
    seed_demo_data(db_session, days=1, random_seed=42, now=NOW)

    reset_demo_data(db_session)

    assert _count(db_session, Building) == 0
    assert _count(db_session, ElectricityUsage) == 0
    assert _count(db_session, User) == 3
