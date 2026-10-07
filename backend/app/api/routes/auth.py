from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DbSession
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenRead
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead
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
