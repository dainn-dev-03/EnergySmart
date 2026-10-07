from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, get_current_user, require_admin_or_manager
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.schemas.electricity_usage import (
    ElectricityUsageCreate,
    ElectricityUsageListParams,
    ElectricityUsageRead,
    ElectricityUsageUpdate,
)
from app.services.electricity_usage_service import ElectricityUsageService

router = APIRouter(
    prefix="/electricity-usages",
    tags=["Electricity Usages"],
    dependencies=[Depends(get_current_user)],
)


def get_usage_service(db: DbSession) -> ElectricityUsageService:
    return ElectricityUsageService(db)


ServiceDep = Annotated[ElectricityUsageService, Depends(get_usage_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get(
    "",
    response_model=PaginatedResponse[ElectricityUsageRead],
    summary="Danh sách dữ liệu điện năng (lọc theo công tơ/phòng/tầng/tòa nhà, khoảng ngày)",
)
def list_usages(
    params: Annotated[ElectricityUsageListParams, Query()], service: ServiceDep
) -> PaginatedResponse[ElectricityUsageRead]:
    return paginated(service.list(params), ElectricityUsageRead)


@router.get(
    "/{usage_id}",
    response_model=ApiResponse[ElectricityUsageRead],
    summary="Chi tiết bản ghi điện năng",
)
def get_usage(usage_id: int, service: ServiceDep) -> ApiResponse[ElectricityUsageRead]:
    return ApiResponse(data=ElectricityUsageRead.model_validate(service.get(usage_id)))


@router.post(
    "",
    response_model=ApiResponse[ElectricityUsageRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Ghi nhận điện năng tiêu thụ trong 1 giờ (cost tự tính theo bảng giá)",
)
def create_usage(
    payload: ElectricityUsageCreate, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ElectricityUsageRead]:
    usage = service.create(payload, current_user)
    return ApiResponse(
        message="Ghi nhận dữ liệu điện năng thành công",
        data=ElectricityUsageRead.model_validate(usage),
    )


@router.put(
    "/{usage_id}",
    response_model=ApiResponse[ElectricityUsageRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật bản ghi điện năng (cost được tính lại)",
)
def update_usage(
    usage_id: int, payload: ElectricityUsageUpdate, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ElectricityUsageRead]:
    usage = service.update(usage_id, payload, current_user)
    return ApiResponse(
        message="Cập nhật dữ liệu điện năng thành công",
        data=ElectricityUsageRead.model_validate(usage),
    )


@router.delete(
    "/{usage_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa bản ghi điện năng",
)
def delete_usage(usage_id: int, service: ServiceDep, current_user: CurrentUser) -> ApiResponse[None]:
    service.delete(usage_id, current_user)
    return ApiResponse(message="Xóa dữ liệu điện năng thành công", data=None)
