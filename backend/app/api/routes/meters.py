from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import DbSession, get_current_user, require_admin_or_manager
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.schemas.meter import MeterCreate, MeterListParams, MeterRead, MeterUpdate
from app.services.meter_service import MeterService

router = APIRouter(prefix="/meters", tags=["Meters"], dependencies=[Depends(get_current_user)])


def get_meter_service(db: DbSession) -> MeterService:
    return MeterService(db)


ServiceDep = Annotated[MeterService, Depends(get_meter_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get("", response_model=PaginatedResponse[MeterRead], summary="Danh sách công tơ")
def list_meters(
    params: Annotated[MeterListParams, Query()], service: ServiceDep
) -> PaginatedResponse[MeterRead]:
    return paginated(service.list(params), MeterRead)


@router.get("/{meter_id}", response_model=ApiResponse[MeterRead], summary="Chi tiết công tơ")
def get_meter(meter_id: int, service: ServiceDep) -> ApiResponse[MeterRead]:
    return ApiResponse(data=MeterRead.model_validate(service.get(meter_id)))


@router.post(
    "",
    response_model=ApiResponse[MeterRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Tạo công tơ",
)
def create_meter(payload: MeterCreate, service: ServiceDep) -> ApiResponse[MeterRead]:
    meter = service.create(payload)
    return ApiResponse(message="Tạo công tơ thành công", data=MeterRead.model_validate(meter))


@router.put(
    "/{meter_id}",
    response_model=ApiResponse[MeterRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật công tơ",
)
def update_meter(
    meter_id: int, payload: MeterUpdate, service: ServiceDep
) -> ApiResponse[MeterRead]:
    meter = service.update(meter_id, payload)
    return ApiResponse(message="Cập nhật công tơ thành công", data=MeterRead.model_validate(meter))


@router.delete(
    "/{meter_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa công tơ (xóa luôn dữ liệu điện và cảnh báo của công tơ)",
)
def delete_meter(meter_id: int, service: ServiceDep) -> ApiResponse[None]:
    service.delete(meter_id)
    return ApiResponse(message="Xóa công tơ thành công", data=None)
