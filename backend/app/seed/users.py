"""Seed user accounts: the admin from SEED_ADMIN_* plus optional demo manager/viewer."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.seed.settings import SeedSettings


@dataclass(frozen=True)
class SeedUser:
    username: str
    email: str
    full_name: str
    role: UserRole
    password: str


def build_seed_users(settings: SeedSettings) -> list[SeedUser]:
    users = [
        SeedUser(
            username=settings.admin_username,
            email=settings.admin_email,
            full_name=settings.admin_full_name,
            role=UserRole.ADMIN,
            password=settings.admin_password.get_secret_value(),
        )
    ]
    if settings.demo_password is not None:
        demo_password = settings.demo_password.get_secret_value()
        users += [
            SeedUser(
                "manager",
                "manager@energysmart.vn",
                "Quản lý tòa nhà",
                UserRole.MANAGER,
                demo_password,
            ),
            SeedUser(
                "viewer",
                "viewer@energysmart.vn",
                "Nhân viên theo dõi",
                UserRole.VIEWER,
                demo_password,
            ),
        ]
    return users


def seed_users(db: Session, settings: SeedSettings) -> list[str]:
    """Create missing accounts; existing ones are left untouched. Returns created usernames."""
    repository = UserRepository(db)
    created: list[str] = []
    for seed_user in build_seed_users(settings):
        if repository.get_by_username(seed_user.username) is not None:
            continue
        repository.add(
            User(
                username=seed_user.username,
                email=seed_user.email,
                full_name=seed_user.full_name,
                role=seed_user.role,
                password_hash=hash_password(seed_user.password),
            )
        )
        created.append(seed_user.username)
    return created
