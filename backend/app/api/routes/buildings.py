from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, get_current_user, require_admin_or_manager
from app.schemas.building import BuildingCreate, BuildingListParams, BuildingRead, BuildingUpdate
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.services.building_service import BuildingService

router = APIRouter(
    prefix="/buildings", tags=["Buildings"], dependencies=[Depends(get_current_user)]
)


def get_building_service(db: DbSession) -> BuildingService:
    return BuildingService(db)


ServiceDep = Annotated[BuildingService, Depends(get_building_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get("", response_model=PaginatedResponse[BuildingRead], summary="Danh sách tòa nhà")
def list_buildings(
    params: Annotated[BuildingListParams, Query()], service: ServiceDep
) -> PaginatedResponse[BuildingRead]:
    return paginated(service.list(params), BuildingRead)


@router.get("/{building_id}", response_model=ApiResponse[BuildingRead], summary="Chi tiết tòa nhà")
def get_building(building_id: int, service: ServiceDep) -> ApiResponse[BuildingRead]:
    return ApiResponse(data=BuildingRead.model_validate(service.get(building_id)))


@router.post(
    "",
    response_model=ApiResponse[BuildingRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Tạo tòa nhà",
)
def create_building(payload: BuildingCreate, service: ServiceDep, current_user: CurrentUser) -> ApiResponse[BuildingRead]:
    building = service.create(payload, current_user)
    return ApiResponse(message="Tạo tòa nhà thành công", data=BuildingRead.model_validate(building))


@router.put(
    "/{building_id}",
    response_model=ApiResponse[BuildingRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật tòa nhà",
)
def update_building(
    building_id: int, payload: BuildingUpdate, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[BuildingRead]:
    building = service.update(building_id, payload, current_user)
    return ApiResponse(
        message="Cập nhật tòa nhà thành công", data=BuildingRead.model_validate(building)
    )


@router.delete(
    "/{building_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa tòa nhà (chỉ khi không còn tầng)",
)
def delete_building(building_id: int, service: ServiceDep, current_user: CurrentUser) -> ApiResponse[None]:
    service.delete(building_id, current_user)
    return ApiResponse(message="Xóa tòa nhà thành công", data=None)
