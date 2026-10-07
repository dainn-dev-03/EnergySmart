from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import AdminOnly, DbSession
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogListParams, AuditLogRead
from app.schemas.common import PaginatedResponse, paginated

router = APIRouter(prefix="/audit-logs", tags=["Audit logs"])


@router.get("", response_model=PaginatedResponse[AuditLogRead])
def list_audit_logs(
    params: Annotated[AuditLogListParams, Query()], db: DbSession, _: AdminOnly
) -> PaginatedResponse[AuditLogRead]:
    return paginated(AuditLogRepository(db).list(params), AuditLogRead)
