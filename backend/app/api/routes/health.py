from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.dependencies import DbSession
from app.schemas.common import ApiResponse
from app.schemas.health import HealthRead
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


def get_health_service(db: DbSession) -> HealthService:
    return HealthService(db, settings.app_version)


@router.get("/health", response_model=ApiResponse[HealthRead], summary="Kiểm tra trạng thái API")
def health_check(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> ApiResponse[HealthRead]:
    return ApiResponse(data=service.check())
