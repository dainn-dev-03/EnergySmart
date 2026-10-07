from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, get_current_user, require_admin_or_manager
from app.schemas.alert import AlertListParams, AlertRead, DetectionResult
from app.schemas.common import ApiResponse, PaginatedResponse, paginated
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"], dependencies=[Depends(get_current_user)])


def get_alert_service(db: DbSession) -> AlertService:
    return AlertService(db)


ServiceDep = Annotated[AlertService, Depends(get_alert_service)]
WRITE_ACCESS = [Depends(require_admin_or_manager)]


@router.get("", response_model=PaginatedResponse[AlertRead], summary="Danh sách cảnh báo")
def list_alerts(
    params: Annotated[AlertListParams, Query()], service: ServiceDep
) -> PaginatedResponse[AlertRead]:
    return paginated(service.list(params), AlertRead)


@router.get("/{alert_id}", response_model=ApiResponse[AlertRead], summary="Chi tiết cảnh báo")
def get_alert(alert_id: int, service: ServiceDep) -> ApiResponse[AlertRead]:
    return ApiResponse(data=AlertRead.model_validate(service.get(alert_id)))


@router.post(
    "/{alert_id}/resolve",
    response_model=ApiResponse[AlertRead],
    dependencies=WRITE_ACCESS,
    summary="Đánh dấu cảnh báo đã xử lý",
)
def resolve_alert(alert_id: int, service: ServiceDep) -> ApiResponse[AlertRead]:
    alert = service.resolve(alert_id)
    return ApiResponse(message="Đã xử lý cảnh báo", data=AlertRead.model_validate(alert))


@router.post(
    "/detect",
    response_model=ApiResponse[DetectionResult],
    dependencies=WRITE_ACCESS,
    summary="Chạy phát hiện tiêu thụ bất thường cho một ngày (mặc định hôm qua)",
)
def detect_alerts(
    service: ServiceDep,
    day: Annotated[date | None, Query(alias="date", description="Ngày cần kiểm tra")] = None,
) -> ApiResponse[DetectionResult]:
    result = service.detect(day)
    return ApiResponse(message=f"Đã tạo {result.created_alerts} cảnh báo mới", data=result)
