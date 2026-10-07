from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.seed.settings import SeedSettings
from app.seed.users import seed_users


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
