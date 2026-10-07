from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_roles
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.core.security import create_access_token, decode_access_token, verify_password
from tests.factories import DEFAULT_PASSWORD, auth_headers, create_user

LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


def test_login_returns_token_and_user(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session)

    response = client.post(LOGIN_URL, json={"username": "admin", "password": DEFAULT_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.access_token_expire_minutes * 60
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "ADMIN"
    assert "password_hash" not in data["user"]
    assert decode_access_token(data["access_token"]).user_id == user.id


def test_login_username_is_case_insensitive(client: TestClient, db_session: Session) -> None:
    create_user(db_session)

    response = client.post(LOGIN_URL, json={"username": " Admin ", "password": DEFAULT_PASSWORD})

    assert response.status_code == 200


@pytest.mark.parametrize("username", ["admin", "unknown"])
def test_login_with_bad_credentials_returns_401(
    client: TestClient, db_session: Session, username: str
) -> None:
    create_user(db_session)

    response = client.post(LOGIN_URL, json={"username": username, "password": "wrong-password"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert body["message"] == "Tên đăng nhập hoặc mật khẩu không đúng"


def test_login_inactive_user_returns_403(client: TestClient, db_session: Session) -> None:
    create_user(db_session, is_active=False)

    response = client.post(LOGIN_URL, json={"username": "admin", "password": DEFAULT_PASSWORD})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_login_validation_error_lists_fields(client: TestClient) -> None:
    response = client.post(LOGIN_URL, json={"username": "admin"})

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "details": [{"field": "password", "message": "Trường này là bắt buộc"}],
    }


def test_me_returns_current_user(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session, username="viewer", role=UserRole.VIEWER)

    response = client.get(ME_URL, headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == user.id
    assert data["role"] == "VIEWER"


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    response = client.get(ME_URL, headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_me_with_expired_token_returns_401(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session)
    expired = create_access_token(user.id, user.role, expires_delta=timedelta(seconds=-1))

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {expired.token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_me_with_token_of_deactivated_user_returns_401(
    client: TestClient, db_session: Session
) -> None:
    user = create_user(db_session)
    headers = auth_headers(user)
    user.is_active = False
    db_session.flush()

    response = client.get(ME_URL, headers=headers)

    assert response.status_code == 401


def test_require_roles_allows_listed_roles_only(db_session: Session) -> None:
    admin = create_user(db_session, username="admin", role=UserRole.ADMIN)
    viewer = create_user(db_session, username="viewer", role=UserRole.VIEWER)
    admin_or_manager = require_roles(UserRole.ADMIN, UserRole.MANAGER)

    assert admin_or_manager(admin) is admin
    with pytest.raises(ForbiddenError):
        admin_or_manager(viewer)


def test_password_is_stored_hashed(db_session: Session) -> None:
    user = create_user(db_session)

    assert user.password_hash != DEFAULT_PASSWORD
    assert user.password_hash.startswith("$argon2")
    assert verify_password(DEFAULT_PASSWORD, user.password_hash)
