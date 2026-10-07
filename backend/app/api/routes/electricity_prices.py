from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DbSession, get_current_user, require_admin
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.schemas.electricity_price import (
    ElectricityPriceCreate,
    ElectricityPriceListParams,
    ElectricityPriceRead,
    ElectricityPriceUpdate,
)
from app.services.electricity_price_service import ElectricityPriceService

router = APIRouter(
    prefix="/electricity-prices",
    tags=["Electricity Prices"],
    dependencies=[Depends(get_current_user)],
)


def get_price_service(db: DbSession) -> ElectricityPriceService:
    return ElectricityPriceService(db)


ServiceDep = Annotated[ElectricityPriceService, Depends(get_price_service)]
WRITE_ACCESS = [Depends(require_admin)]


@router.get(
    "", response_model=PaginatedResponse[ElectricityPriceRead], summary="Danh sách bảng giá điện"
)
def list_prices(
    params: Annotated[ElectricityPriceListParams, Query()], service: ServiceDep
) -> PaginatedResponse[ElectricityPriceRead]:
    return paginated(service.list(params), ElectricityPriceRead)


@router.get(
    "/{price_id}", response_model=ApiResponse[ElectricityPriceRead], summary="Chi tiết bảng giá"
)
def get_price(price_id: int, service: ServiceDep) -> ApiResponse[ElectricityPriceRead]:
    return ApiResponse(data=ElectricityPriceRead.model_validate(service.get(price_id)))


@router.post(
    "",
    response_model=ApiResponse[ElectricityPriceRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_ACCESS,
    summary="Tạo bảng giá (ADMIN)",
)
def create_price(
    payload: ElectricityPriceCreate, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ElectricityPriceRead]:
    price = service.create(payload, current_user)
    return ApiResponse(
        message="Tạo bảng giá điện thành công", data=ElectricityPriceRead.model_validate(price)
    )


@router.put(
    "/{price_id}",
    response_model=ApiResponse[ElectricityPriceRead],
    dependencies=WRITE_ACCESS,
    summary="Cập nhật bảng giá (ADMIN)",
)
def update_price(
    price_id: int, payload: ElectricityPriceUpdate, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ElectricityPriceRead]:
    price = service.update(price_id, payload, current_user)
    return ApiResponse(
        message="Cập nhật bảng giá điện thành công",
        data=ElectricityPriceRead.model_validate(price),
    )


@router.delete(
    "/{price_id}",
    response_model=ApiResponse[None],
    dependencies=WRITE_ACCESS,
    summary="Xóa bảng giá (ADMIN)",
)
def delete_price(price_id: int, service: ServiceDep, current_user: CurrentUser) -> ApiResponse[None]:
    service.delete(price_id, current_user)
    return ApiResponse(message="Xóa bảng giá điện thành công", data=None)
