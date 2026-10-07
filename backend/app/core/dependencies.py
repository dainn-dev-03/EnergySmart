"""Shared FastAPI dependencies: DB session, current user and role checks."""

from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]

# auto_error=False: missing credentials go through UnauthorizedError and the error envelope.
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Dán access_token nhận được từ POST /api/v1/auth/login",
)


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    return AuthService(UserRepository(db)).get_user_from_token(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    allowed_roles = frozenset(roles)

    def check_role(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError()
        return current_user

    return check_role


require_admin_or_manager = require_roles(UserRole.ADMIN, UserRole.MANAGER)
require_admin = require_roles(UserRole.ADMIN)

AdminOrManager = Annotated[User, Depends(require_admin_or_manager)]
AdminOnly = Annotated[User, Depends(require_admin)]
