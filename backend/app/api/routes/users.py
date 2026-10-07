from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.dependencies import AdminOnly, DbSession
from app.core.enums import UserRole
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models import AuditLog, User
from app.repositories.user_repository import UserRepository
from app.schemas.common import ApiResponse
from app.schemas.user import PasswordReset, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def _target(db: DbSession, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("Không tìm thấy người dùng")
    return user


@router.get("", response_model=ApiResponse[list[UserRead]])
def list_users(db: DbSession, _: AdminOnly) -> ApiResponse[list[UserRead]]:
    return ApiResponse(data=[UserRead.model_validate(user) for user in db.scalars(select(User).order_by(User.username)).all()])


@router.post("", response_model=ApiResponse[UserRead])
def create_user(payload: UserCreate, db: DbSession, current: AdminOnly) -> ApiResponse[UserRead]:
    repo = UserRepository(db)
    if repo.get_by_username(payload.username):
        raise ConflictError.for_field("username", "Tên đăng nhập đã tồn tại")
    if db.scalar(select(User).where(func.lower(User.email) == payload.email.lower())):
        raise ConflictError.for_field("email", "Email đã tồn tại")
    user = User(username=payload.username, email=payload.email, full_name=payload.full_name, role=payload.role, password_hash=hash_password(payload.password))
    db.add(user); db.flush(); db.add(AuditLog(user_id=current.id, action="CREATE_USER", entity_type="users", entity_id=user.id, entity_label=user.username, changes={"role": [None, user.role.value]})); db.commit(); db.refresh(user)
    return ApiResponse(message="Tạo người dùng thành công", data=UserRead.model_validate(user))


@router.put("/{user_id}", response_model=ApiResponse[UserRead])
def update_user(user_id: int, payload: UserUpdate, db: DbSession, current: AdminOnly) -> ApiResponse[UserRead]:
    user = _target(db, user_id)
    if user.id == current.id and payload.role is not None and payload.role != current.role:
        raise BusinessRuleError("Không thể tự thay đổi quyền của chính mình")
    if user.role is UserRole.ADMIN and payload.role is not None and payload.role is not UserRole.ADMIN and UserRepository(db).admin_count() <= 1:
        raise BusinessRuleError("Không thể hạ quyền ADMIN cuối cùng")
    for field, value in payload.model_dump(exclude_none=True).items(): setattr(user, field, value)
    db.add(AuditLog(user_id=current.id, action="UPDATE_USER", entity_type="users", entity_id=user.id, entity_label=user.username, changes=None))
    db.commit(); db.refresh(user)
    return ApiResponse(message="Cập nhật người dùng thành công", data=UserRead.model_validate(user))


@router.post("/{user_id}/deactivate", response_model=ApiResponse[UserRead])
def deactivate(user_id: int, db: DbSession, current: AdminOnly) -> ApiResponse[UserRead]:
    user = _target(db, user_id)
    if user.id == current.id: raise BusinessRuleError("Không thể tự khóa tài khoản")
    if user.role is UserRole.ADMIN and UserRepository(db).admin_count() <= 1: raise BusinessRuleError("Không thể khóa ADMIN cuối cùng")
    user.is_active = False; db.add(AuditLog(user_id=current.id, action="DEACTIVATE_USER", entity_type="users", entity_id=user.id, entity_label=user.username, changes=None)); db.commit(); db.refresh(user)
    return ApiResponse(message="Đã khóa tài khoản", data=UserRead.model_validate(user))


@router.post("/{user_id}/reset-password", response_model=ApiResponse[None])
def reset_password(user_id: int, payload: PasswordReset, db: DbSession, current: AdminOnly) -> ApiResponse[None]:
    user = _target(db, user_id)
    user.password_hash = hash_password(payload.new_password)
    db.add(AuditLog(user_id=current.id, action="RESET_PASSWORD", entity_type="users", entity_id=user.id, entity_label=user.username, changes=None))
    db.commit()
    return ApiResponse(message="Đặt lại mật khẩu thành công", data=None)


@router.post("/{user_id}/activate", response_model=ApiResponse[UserRead])
def activate(user_id: int, db: DbSession, current: AdminOnly) -> ApiResponse[UserRead]:
    user = _target(db, user_id); user.is_active = True; db.add(AuditLog(user_id=current.id, action="ACTIVATE_USER", entity_type="users", entity_id=user.id, entity_label=user.username, changes=None)); db.commit(); db.refresh(user)
    return ApiResponse(message="Đã mở khóa tài khoản", data=UserRead.model_validate(user))
