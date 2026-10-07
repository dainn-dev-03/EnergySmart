from functools import cache

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenRead
from app.schemas.user import UserRead

_INVALID_CREDENTIALS_MESSAGE = "Tên đăng nhập hoặc mật khẩu không đúng"


@cache
def _dummy_password_hash() -> str:
    """Hash checked for unknown usernames, so response time does not reveal which exist."""
    return hash_password("energysmart-timing-guard")


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def login(self, username: str, password: str) -> TokenRead:
        user = self.users.get_by_username(username)
        if user is None:
            verify_password(password, _dummy_password_hash())
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")
        if not user.is_active:
            raise ForbiddenError("Tài khoản đã bị vô hiệu hóa", code="ACCOUNT_DISABLED")

        access_token = create_access_token(user.id, user.role)
        return TokenRead(
            access_token=access_token.token,
            expires_in=access_token.expires_in,
            user=UserRead.model_validate(user),
        )

    def get_user_from_token(self, token: str) -> User:
        payload = decode_access_token(token)
        user = self.users.get(payload.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(
                "Tài khoản không tồn tại hoặc đã bị vô hiệu hóa", code="INVALID_TOKEN"
            )
        return user
