"""Password hashing (Argon2 via pwdlib) and JWT access tokens (PyJWT)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

_password_hash = PasswordHash.recommended()

_TOKEN_TYPE = "access"


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_in: int  # seconds


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    role: str


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def create_access_token(
    user_id: int, role: str, expires_delta: timedelta | None = None
) -> AccessToken:
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    issued_at = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "role": role,
        "type": _TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + lifetime,
    }
    token = jwt.encode(
        claims, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return AccessToken(token=token, expires_in=int(lifetime.total_seconds()))


def decode_access_token(token: str) -> TokenPayload:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(
            "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", code="TOKEN_EXPIRED"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Token không hợp lệ", code="INVALID_TOKEN") from exc

    subject = str(claims["sub"])
    if claims.get("type") != _TOKEN_TYPE or not subject.isdigit():
        raise UnauthorizedError("Token không hợp lệ", code="INVALID_TOKEN")
    return TokenPayload(user_id=int(subject), role=str(claims.get("role", "")))
