from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, get_current_user
from app.schemas.analytics import DailyPoint, MonthlyPoint, RoomConsumption
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardSummary, FloorTrend
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)]
)


def get_dashboard_service(db: DbSession) -> DashboardService:
    return DashboardService(db)


ServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
BuildingFilter = Annotated[int | None, Query(description="Lọc theo tòa nhà (mặc định tất cả)")]


@router.get(
    "/summary",
    response_model=ApiResponse[DashboardSummary],
    summary="Thẻ tổng quan: hôm nay, tháng này, công tơ hoạt động, cảnh báo",
)
def get_summary(
    service: ServiceDep, building_id: BuildingFilter = None
) -> ApiResponse[DashboardSummary]:
    return ApiResponse(data=service.summary(building_id))


@router.get(
    "/daily", response_model=ApiResponse[list[DailyPoint]], summary="Tiêu thụ N ngày gần nhất"
)
def get_daily(
    service: ServiceDep,
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    building_id: BuildingFilter = None,
) -> ApiResponse[list[DailyPoint]]:
    return ApiResponse(data=service.daily(days, building_id))


@router.get(
    "/monthly", response_model=ApiResponse[list[MonthlyPoint]], summary="Tiêu thụ N tháng gần nhất"
)
def get_monthly(
    service: ServiceDep,
    months: Annotated[int, Query(ge=1, le=24)] = 12,
    building_id: BuildingFilter = None,
) -> ApiResponse[list[MonthlyPoint]]:
    return ApiResponse(data=service.monthly(months, building_id))


@router.get(
    "/by-floor",
    response_model=ApiResponse[list[FloorTrend]],
    summary="Tiêu thụ theo tầng: 7 ngày gần nhất so với 7 ngày trước",
)
def get_by_floor(
    service: ServiceDep, building_id: BuildingFilter = None
) -> ApiResponse[list[FloorTrend]]:
    return ApiResponse(data=service.floor_trends(building_id))


@router.get(
    "/by-room",
    response_model=ApiResponse[list[RoomConsumption]],
    summary="Các phòng tiêu thụ nhiều nhất trong tháng",
)
def get_by_room(
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    building_id: BuildingFilter = None,
) -> ApiResponse[list[RoomConsumption]]:
    return ApiResponse(data=service.top_rooms(limit, building_id))


@router.get(
    "/cost", response_model=ApiResponse[list[MonthlyPoint]], summary="Chi phí điện theo tháng"
)
def get_cost(
    service: ServiceDep,
    months: Annotated[int, Query(ge=1, le=24)] = 6,
    building_id: BuildingFilter = None,
) -> ApiResponse[list[MonthlyPoint]]:
    return ApiResponse(data=service.monthly(months, building_id))
