from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import AuditLog
from app.repositories.base import BaseRepository
from app.schemas.audit_log import AuditLogListParams
from app.schemas.common import Page


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog
    load_options = (joinedload(AuditLog.user),)
    sort_columns = {"created_at": AuditLog.created_at}

    def list(self, params: AuditLogListParams) -> Page[AuditLog]:
        filters = []
        for column, value in ((AuditLog.user_id, params.user_id), (AuditLog.action, params.action), (AuditLog.entity_type, params.entity_type), (AuditLog.entity_id, params.entity_id)):
            if value is not None:
                filters.append(column == value)
        if params.from_date:
            filters.append(AuditLog.created_at >= params.from_date)
        if params.to_date:
            filters.append(AuditLog.created_at <= params.to_date)
        return self._list(params, filters)
