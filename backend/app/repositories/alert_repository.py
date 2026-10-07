from app.models import Alert
from app.repositories.base import BaseRepository
from app.repositories.scopes import meter_id_scope


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    def count_unresolved(self, building_id: int | None = None) -> int:
        return self._count(
            Alert.is_resolved.is_(False),
            *meter_id_scope(Alert.meter_id, building_id=building_id),
        )
