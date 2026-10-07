from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import DbSession, get_current_user, require_admin_or_manager
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.schemas.floor import FloorCreate, FloorListParams, FloorRead, FloorUpdate
from app.services.floor_service import FloorService

router = APIRouter(prefix="/floors", tags=["Floors"], dependencies=[Depends(get_current_user)])


def get_floor_service(db: DbSession) -> FloorService:
    return FloorService(db)


ServiceDep = Annotated[FloorService, Depends(get_floor_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get("", response_model=PaginatedResponse[FloorRead], summary="Danh sách tầng")
def list_floors(
    params: Annotated[FloorListParams, Query()], service: ServiceDep
) -> PaginatedResponse[FloorRead]:
    return paginated(service.list(params), FloorRead)


@router.get("/{floor_id}", response_model=ApiResponse[FloorRead], summary="Chi tiết tầng")
def get_floor(floor_id: int, service: ServiceDep) -> ApiResponse[FloorRead]:
    return ApiResponse(data=FloorRead.model_validate(service.get(floor_id)))


@router.post(
    "",
    response_model=ApiResponse[FloorRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Tạo tầng",
)
def create_floor(payload: FloorCreate, service: ServiceDep) -> ApiResponse[FloorRead]:
    floor = service.create(payload)
    return ApiResponse(message="Tạo tầng thành công", data=FloorRead.model_validate(floor))


@router.put(
    "/{floor_id}",
    response_model=ApiResponse[FloorRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật tầng",
)
def update_floor(
    floor_id: int, payload: FloorUpdate, service: ServiceDep
) -> ApiResponse[FloorRead]:
    floor = service.update(floor_id, payload)
    return ApiResponse(message="Cập nhật tầng thành công", data=FloorRead.model_validate(floor))


@router.delete(
    "/{floor_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa tầng (chỉ khi không còn phòng)",
)
def delete_floor(floor_id: int, service: ServiceDep) -> ApiResponse[None]:
    service.delete(floor_id)
    return ApiResponse(message="Xóa tầng thành công", data=None)
