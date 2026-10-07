from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, get_current_user
from app.schemas.analytics import (
    Comparison,
    ComparisonParams,
    DailyPoint,
    DateRangeParams,
    FloorConsumption,
    HourlyPoint,
    MonthlyPoint,
    RoomBreakdownParams,
    RoomConsumption,
)
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics", tags=["Analytics"], dependencies=[Depends(get_current_user)]
)


def get_analytics_service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(db)


ServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
RangeQuery = Annotated[DateRangeParams, Query()]


@router.get(
    "/daily",
    response_model=ApiResponse[list[DailyPoint]],
    summary="Tiêu thụ theo ngày (mặc định 30 ngày gần nhất)",
)
def get_daily(params: RangeQuery, service: ServiceDep) -> ApiResponse[list[DailyPoint]]:
    return ApiResponse(data=service.daily(params))


@router.get(
    "/monthly",
    response_model=ApiResponse[list[MonthlyPoint]],
    summary="Tiêu thụ theo tháng (mặc định 12 tháng gần nhất)",
)
def get_monthly(params: RangeQuery, service: ServiceDep) -> ApiResponse[list[MonthlyPoint]]:
    return ApiResponse(data=service.monthly(params))


@router.get(
    "/hourly",
    response_model=ApiResponse[list[HourlyPoint]],
    summary="Biểu đồ tải trung bình theo giờ (ngày thường / cuối tuần)",
)
def get_hourly(params: RangeQuery, service: ServiceDep) -> ApiResponse[list[HourlyPoint]]:
    return ApiResponse(data=service.hourly(params))


@router.get(
    "/by-floor",
    response_model=ApiResponse[list[FloorConsumption]],
    summary="Tiêu thụ và tỷ trọng theo tầng",
)
def get_by_floor(params: RangeQuery, service: ServiceDep) -> ApiResponse[list[FloorConsumption]]:
    return ApiResponse(data=service.by_floor(params))


@router.get(
    "/by-room",
    response_model=ApiResponse[list[RoomConsumption]],
    summary="Tiêu thụ và tỷ trọng theo phòng (sắp xếp giảm dần)",
)
def get_by_room(
    params: Annotated[RoomBreakdownParams, Query()], service: ServiceDep
) -> ApiResponse[list[RoomConsumption]]:
    return ApiResponse(data=service.by_room(params))


@router.get(
    "/comparison",
    response_model=ApiResponse[Comparison],
    summary="So sánh kỳ hiện tại với kỳ trước (cùng khoảng thời gian đã trôi qua)",
)
def get_comparison(
    params: Annotated[ComparisonParams, Query()], service: ServiceDep
) -> ApiResponse[Comparison]:
    return ApiResponse(data=service.comparison(params))
