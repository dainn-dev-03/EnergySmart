from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import DbSession, get_current_user, require_admin_or_manager
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.schemas.room import RoomCreate, RoomListParams, RoomRead, RoomUpdate
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"], dependencies=[Depends(get_current_user)])


def get_room_service(db: DbSession) -> RoomService:
    return RoomService(db)


ServiceDep = Annotated[RoomService, Depends(get_room_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get("", response_model=PaginatedResponse[RoomRead], summary="Danh sách phòng")
def list_rooms(
    params: Annotated[RoomListParams, Query()], service: ServiceDep
) -> PaginatedResponse[RoomRead]:
    return paginated(service.list(params), RoomRead)


@router.get("/{room_id}", response_model=ApiResponse[RoomRead], summary="Chi tiết phòng")
def get_room(room_id: int, service: ServiceDep) -> ApiResponse[RoomRead]:
    return ApiResponse(data=RoomRead.model_validate(service.get(room_id)))


@router.post(
    "",
    response_model=ApiResponse[RoomRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Tạo phòng",
)
def create_room(payload: RoomCreate, service: ServiceDep) -> ApiResponse[RoomRead]:
    room = service.create(payload)
    return ApiResponse(message="Tạo phòng thành công", data=RoomRead.model_validate(room))


@router.put(
    "/{room_id}",
    response_model=ApiResponse[RoomRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật phòng",
)
def update_room(room_id: int, payload: RoomUpdate, service: ServiceDep) -> ApiResponse[RoomRead]:
    room = service.update(room_id, payload)
    return ApiResponse(message="Cập nhật phòng thành công", data=RoomRead.model_validate(room))


@router.delete(
    "/{room_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa phòng (chỉ khi không còn công tơ)",
)
def delete_room(room_id: int, service: ServiceDep) -> ApiResponse[None]:
    service.delete(room_id)
    return ApiResponse(message="Xóa phòng thành công", data=None)
