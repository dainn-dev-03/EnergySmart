"""Abnormal consumption alerts.

A meter's day is abnormal when its consumption exceeds the average of the same day type
(weekday or weekend) over the previous `alert_baseline_days` days by the configured ratios.
"""

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AlertSeverity, AlertType, MeterStatus
from app.core.exceptions import ConflictError, InvalidInputError, NotFoundError
from app.core.timezone import local_day_end_exclusive, local_day_start, local_now
from app.models import Alert, AuditLog, Meter, User
from app.repositories.alert_repository import AlertRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.meter_repository import MeterRepository
from app.schemas.alert import AlertListParams, DetectionResult
from app.schemas.common import Page

_KWH = Decimal("0.001")


def classify_ratio(ratio: float) -> AlertSeverity | None:
    if ratio >= settings.alert_ratio_critical:
        return AlertSeverity.CRITICAL
    if ratio >= settings.alert_ratio_warning:
        return AlertSeverity.WARNING
    if ratio >= settings.alert_ratio_info:
        return AlertSeverity.INFO
    return None


def _is_weekend(day: date) -> bool:
    return day.weekday() >= 5


@dataclass(frozen=True)
class DayEvaluation:
    actual: Decimal
    baseline: Decimal
    ratio: float
    severity: AlertSeverity | None


def evaluate_day(daily_kwh: Mapping[date, Decimal], day: date) -> DayEvaluation | None:
    """Compare `day` with previous days of the same type; None when there is not enough data."""
    actual = daily_kwh.get(day)
    if actual is None:
        return None
    references = [
        daily_kwh[previous]
        for offset in range(1, settings.alert_baseline_days + 1)
        if (previous := day - timedelta(days=offset)) in daily_kwh
        and _is_weekend(previous) == _is_weekend(day)
    ]
    if len(references) < settings.alert_min_reference_days:
        return None
    baseline = sum(references, Decimal(0)) / len(references)
    if baseline <= 0:
        return None
    ratio = float(actual / baseline)
    return DayEvaluation(actual, baseline, ratio, classify_ratio(ratio))


def _vn_number(value: Decimal | float) -> str:
    """One decimal with a Vietnamese decimal comma, e.g. 2,5."""
    return f"{value:.1f}".replace(".", ",")


def _message(meter: Meter, day: date, evaluation: DayEvaluation) -> str:
    return (
        f"Công tơ {meter.meter_code} ({meter.room.name}, {meter.room.floor.name}) tiêu thụ "
        f"{_vn_number(evaluation.actual)} kWh ngày {day:%d/%m/%Y}, "
        f"gấp {_vn_number(evaluation.ratio)} lần "
        f"mức trung bình {_vn_number(evaluation.baseline)} kWh"
    )


class AlertService:
    def __init__(self, db: Session, now: Callable[[], datetime] = local_now) -> None:
        self.db = db
        self.alerts = AlertRepository(db)
        self.meters = MeterRepository(db)
        self.analytics = AnalyticsRepository(db)
        self._now = now

    def list(self, params: AlertListParams) -> Page[Alert]:
        return self.alerts.list(params)

    def get(self, alert_id: int) -> Alert:
        alert = self.alerts.get(alert_id)
        if alert is None:
            raise NotFoundError(f"Không tìm thấy cảnh báo có id={alert_id}")
        return alert

    def resolve(self, alert_id: int, actor: User) -> Alert:
        alert = self.get(alert_id)
        if alert.is_resolved:
            raise ConflictError("Cảnh báo đã được xử lý trước đó")
        alert.is_resolved = True
        alert.resolved_at = self._now()
        alert.resolved_by_id = actor.id
        self.db.add(AuditLog(user_id=actor.id, action="RESOLVE", entity_type="alerts", entity_id=alert.id, entity_label=alert.message, changes={"is_resolved": [False, True]}))
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def detect(self, day: date | None) -> DetectionResult:
        """Run detection for one complete day (default: yesterday) and commit."""
        result = self.detect_range(day or self._yesterday(), day or self._yesterday())
        self.db.commit()
        return result

    def detect_range(self, first_day: date, last_day: date) -> DetectionResult:
        """Evaluate every ACTIVE meter on each complete day of the range. Does not commit."""
        if last_day > self._yesterday():
            raise InvalidInputError.for_field(
                "date", "Chỉ phát hiện được cho ngày đã kết thúc (tối đa là hôm qua)"
            )
        meters = self.meters.list_by_status(MeterStatus.ACTIVE)
        daily_kwh = self._daily_kwh_by_meter(meters, first_day, last_day)

        rows: list[dict[str, Any]] = []
        for meter in meters:
            meter_days = daily_kwh.get(meter.id, {})
            day = first_day
            while day <= last_day:
                evaluation = evaluate_day(meter_days, day)
                if evaluation is not None and evaluation.severity is not None:
                    rows.append(self._alert_row(meter, day, evaluation))
                day += timedelta(days=1)

        created = self.alerts.insert_new(rows)
        return DetectionResult(
            from_date=first_day,
            to_date=last_day,
            evaluated_meters=len(meters),
            created_alerts=len(created),
            by_severity=dict(Counter(created)),
        )

    def _daily_kwh_by_meter(
        self, meters: Sequence[Meter], first_day: date, last_day: date
    ) -> dict[int, dict[date, Decimal]]:
        reference_start = first_day - timedelta(days=settings.alert_baseline_days)
        totals = self.analytics.daily_totals_by_meter(
            local_day_start(reference_start),
            local_day_end_exclusive(last_day),
            [meter.id for meter in meters],
        )
        by_meter: dict[int, dict[date, Decimal]] = defaultdict(dict)
        for total in totals:
            by_meter[total.meter_id][total.day] = total.kwh
        return by_meter

    @staticmethod
    def _alert_row(meter: Meter, day: date, evaluation: DayEvaluation) -> dict[str, Any]:
        return {
            "meter_id": meter.id,
            "alert_type": AlertType.HIGH_CONSUMPTION,
            "severity": evaluation.severity,
            "message": _message(meter, day, evaluation),
            "threshold_value": (
                evaluation.baseline * Decimal(str(settings.alert_ratio_info))
            ).quantize(_KWH),
            "actual_value": evaluation.actual.quantize(_KWH),
            "usage_date": day,
            # Raised when the day closes, so history created by the seed reads naturally.
            "created_at": local_day_end_exclusive(day),
        }

    def _yesterday(self) -> date:
        return self._now().date() - timedelta(days=1)
