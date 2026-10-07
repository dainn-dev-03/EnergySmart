from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import InvalidInputError
from app.core.security import hash_password, verify_password
from app.models import AuditLog
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenRead
from app.schemas.common import ApiResponse
from app.schemas.user import PasswordChange, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(UserRepository(db))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login", response_model=ApiResponse[TokenRead], summary="Đăng nhập")
def login(payload: LoginRequest, service: AuthServiceDep) -> ApiResponse[TokenRead]:
    token = service.login(payload.username, payload.password)
    return ApiResponse(message="Đăng nhập thành công", data=token)


@router.get("/me", response_model=ApiResponse[UserRead], summary="Thông tin người dùng hiện tại")
def read_current_user(current_user: CurrentUser) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserRead.model_validate(current_user))


@router.put("/me/password", response_model=ApiResponse[None])
def change_password(payload: PasswordChange, current_user: CurrentUser, db: DbSession) -> ApiResponse[None]:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise InvalidInputError.for_field("current_password", "Mật khẩu hiện tại không đúng")
    current_user.password_hash = hash_password(payload.new_password)
    db.add(AuditLog(user_id=current_user.id, action="CHANGE_PASSWORD", entity_type="users", entity_id=current_user.id, entity_label=current_user.username, changes=None))
    db.commit()
    return ApiResponse(message="Đổi mật khẩu thành công", data=None)
