from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from app.core.enums import AlertSeverity
from app.models import Alert, Floor, Meter, Room
from app.repositories.base import BaseRepository
from app.repositories.scopes import meter_id_scope
from app.schemas.alert import AlertListParams
from app.schemas.common import Page


class AlertRepository(BaseRepository[Alert]):
    model = Alert
    load_options = (
        joinedload(Alert.meter)
        .joinedload(Meter.room)
        .joinedload(Room.floor)
        .joinedload(Floor.building),
    )
    sort_columns = {
        "created_at": Alert.created_at,
        "usage_date": Alert.usage_date,
        "actual_value": Alert.actual_value,
    }

    def list(self, params: AlertListParams) -> Page[Alert]:
        filters = meter_id_scope(
            Alert.meter_id,
            meter_id=params.meter_id,
            room_id=params.room_id,
            floor_id=params.floor_id,
            building_id=params.building_id,
        )
        if params.is_resolved is not None:
            filters.append(Alert.is_resolved.is_(params.is_resolved))
        if params.severity is not None:
            filters.append(Alert.severity == params.severity)
        if params.from_date is not None:
            filters.append(Alert.usage_date >= params.from_date)
        if params.to_date is not None:
            filters.append(Alert.usage_date <= params.to_date)
        return self._list(params, filters)

    def count_unresolved(
        self,
        building_id: int | None = None,
        severity: AlertSeverity | None = None,
    ) -> int:
        conditions = [
            Alert.is_resolved.is_(False),
            *meter_id_scope(Alert.meter_id, building_id=building_id),
        ]
        if severity is not None:
            conditions.append(Alert.severity == severity)
        return self._count(*conditions)

    def insert_new(self, rows: Sequence[Mapping[str, Any]]) -> Sequence[AlertSeverity]:
        """Insert alerts, silently skipping (meter, type, day) combinations that already exist.

        Returns the severities of the rows actually inserted.
        """
        if not rows:
            return []
        statement = (
            insert(Alert)
            .values(list(rows))
            .on_conflict_do_nothing(index_elements=["meter_id", "alert_type", "usage_date"])
            .returning(Alert.severity)
        )
        return self.db.scalars(statement).all()

    def resolve_before(self, day: date) -> int:
        """Mark open alerts of days before `day` as resolved a few hours after creation."""
        statement = (
            update(Alert)
            .where(Alert.is_resolved.is_(False), Alert.usage_date < day)
            .values(is_resolved=True, resolved_at=Alert.created_at + timedelta(hours=4))
            .returning(Alert.id)
        )
        return len(self.db.scalars(statement).all())
