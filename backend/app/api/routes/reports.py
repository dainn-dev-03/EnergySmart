from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.dependencies import DbSession, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.report import ConsumptionReport, ConsumptionReportParams
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(get_current_user)])


def get_report_service(db: DbSession) -> ReportService:
    return ReportService(db)


ServiceDep = Annotated[ReportService, Depends(get_report_service)]
ReportQuery = Annotated[ConsumptionReportParams, Query()]


@router.get(
    "/consumption",
    response_model=ApiResponse[ConsumptionReport],
    summary="Báo cáo tiêu thụ theo tầng/phòng/công tơ (mặc định từ đầu tháng)",
)
def consumption_report(params: ReportQuery, service: ServiceDep) -> ApiResponse[ConsumptionReport]:
    return ApiResponse(data=service.consumption(params))


@router.get(
    "/consumption/export",
    summary="Xuất báo cáo tiêu thụ ra file CSV",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}, "description": "File CSV (UTF-8 BOM)"}},
)
def export_consumption_report(params: ReportQuery, service: ServiceDep) -> Response:
    filename, content = service.consumption_csv(params)
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
