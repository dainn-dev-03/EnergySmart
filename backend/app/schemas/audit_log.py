from datetime import datetime
from typing import Any, Literal

from app.schemas.common import ListParams, OrmModel, SortOrder
from app.schemas.user import UserSummary


class AuditLogRead(OrmModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    entity_label: str
    changes: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
    user: UserSummary | None


class AuditLogListParams(ListParams):
    user_id: int | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    sort_by: Literal["created_at"] = "created_at"
    sort_order: SortOrder = SortOrder.DESC
