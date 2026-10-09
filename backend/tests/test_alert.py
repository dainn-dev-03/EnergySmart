from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AlertSeverity, AlertType
from app.core.exceptions import InvalidInputError
from app.models import Alert, AuditLog
from app.services.alert_service import AlertService, classify_ratio, evaluate_day
from tests.analytics_fixtures import NOW, TwoFloors, add_usage, build_two_floors, local

URL = "/api/v1/alerts"
TUESDAY = date(2025, 6, 3)  # "yesterday" relative to NOW


def _service(db: Session) -> AlertService:
    return AlertService(db, now=lambda: NOW)


def _history(db: Session, data: TwoFloors, spike_kwh: str) -> None:
    """14 days of normal usage (10 kWh weekdays, 4 kWh weekends) then `spike_kwh` on TUESDAY."""
    for offset in range(1, 15):
        day = TUESDAY - timedelta(days=offset)
        kwh = "4.000" if day.weekday() >= 5 else "10.000"
        for meter in (data.meter_a, data.meter_b):
            add_usage(db, meter, local(day.day, 9, month=day.month), kwh)
    add_usage(db, data.meter_a, local(TUESDAY.day, 9), spike_kwh)
    add_usage(db, data.meter_b, local(TUESDAY.day, 9), "10.000")


def test_classify_ratio_thresholds() -> None:
    assert classify_ratio(1.19) is None
    assert classify_ratio(1.2) is AlertSeverity.INFO
    assert classify_ratio(1.5) is AlertSeverity.WARNING
    assert classify_ratio(2.0) is AlertSeverity.CRITICAL


def test_evaluate_day_compares_with_same_day_type_only() -> None:
    monday = date(2025, 6, 2)
    daily = {monday - timedelta(days=offset): Decimal(10) for offset in (3, 4, 5, 6, 7)}
    daily |= {date(2025, 5, 31): Decimal(1), date(2025, 6, 1): Decimal(1)}  # weekend, ignored
    daily[monday] = Decimal(16)

    evaluation = evaluate_day(daily, monday)

    assert evaluation is not None
    assert evaluation.baseline == Decimal(10)
    assert evaluation.severity is AlertSeverity.WARNING


def test_evaluate_day_needs_enough_reference_days() -> None:
    monday = date(2025, 6, 2)
    daily = {monday: Decimal(50), monday - timedelta(days=7): Decimal(10)}

    assert evaluate_day(daily, monday) is None


def test_detect_creates_alert_with_readable_message_once(db_session: Session) -> None:
    data = build_two_floors(db_session)
    _history(db_session, data, spike_kwh="25.000")

    first = _service(db_session).detect_range(TUESDAY, TUESDAY)
    second = _service(db_session).detect_range(TUESDAY, TUESDAY)

    assert (first.evaluated_meters, first.created_alerts) == (2, 1)
    assert first.by_severity == {AlertSeverity.CRITICAL: 1}
    assert second.created_alerts == 0
    alert = db_session.scalars(select(Alert)).one()
    assert alert.meter_id == data.meter_a.id
    assert alert.actual_value == Decimal("25.000")
    assert alert.threshold_value == Decimal("12.000")
    assert alert.message == (
        "Công tơ MA (Phòng A, Tầng 1) tiêu thụ 25,0 kWh ngày 03/06/2025, "
        "gấp 2,5 lần mức trung bình 10,0 kWh"
    )


def test_detect_rejects_days_that_are_not_finished(db_session: Session) -> None:
    with pytest.raises(InvalidInputError):
        _service(db_session).detect_range(NOW.date(), NOW.date())


def test_list_filter_and_resolve_alerts(
    client: TestClient,
    db_session: Session,
    manager_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    data = build_two_floors(db_session)
    _history(db_session, data, spike_kwh="16.000")
    _service(db_session).detect_range(TUESDAY, TUESDAY)
    alert = db_session.scalars(select(Alert)).one()

    listed = client.get(URL, params={"severity": "WARNING"}, headers=viewer_headers).json()
    viewer_resolve = client.post(f"{URL}/{alert.id}/resolve", headers=viewer_headers)
    resolved = client.post(f"{URL}/{alert.id}/resolve", headers=manager_headers)
    again = client.post(f"{URL}/{alert.id}/resolve", headers=manager_headers)
    open_alerts = client.get(URL, params={"is_resolved": False}, headers=viewer_headers).json()

    assert [item["id"] for item in listed["data"]] == [alert.id]
    assert listed["data"][0]["meter"]["room"]["floor"]["building"]["code"] == "ES-01"
    assert viewer_resolve.status_code == 403
    assert resolved.status_code == 200
    assert resolved.json()["data"]["is_resolved"] is True
    assert resolved.json()["data"]["resolved_at"] is not None
    assert again.status_code == 409
    assert open_alerts["pagination"]["total"] == 0


def test_count_unresolved_alerts_filters_by_severity(db_session: Session) -> None:
    data = build_two_floors(db_session)
    db_session.add_all(
        [
            Alert(
                meter_id=data.meter_a.id,
                alert_type=AlertType.HIGH_CONSUMPTION,
                severity=AlertSeverity.CRITICAL,
                message="Critical open",
                usage_date=date(2025, 6, 1),
                is_resolved=False,
            ),
            Alert(
                meter_id=data.meter_a.id,
                alert_type=AlertType.HIGH_CONSUMPTION,
                severity=AlertSeverity.WARNING,
                message="Warning open",
                usage_date=date(2025, 6, 2),
                is_resolved=False,
            ),
            Alert(
                meter_id=data.meter_a.id,
                alert_type=AlertType.HIGH_CONSUMPTION,
                severity=AlertSeverity.CRITICAL,
                message="Critical resolved",
                usage_date=date(2025, 6, 3),
                is_resolved=True,
            ),
        ]
    )

    assert _service(db_session).alerts.count_unresolved(
        severity=AlertSeverity.CRITICAL
    ) == 1


def test_detect_endpoint(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    response = client.post(f"{URL}/detect", params={"date": "2025-01-15"}, headers=admin_headers)
    future = client.post(f"{URL}/detect", params={"date": "2999-01-01"}, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["data"]["created_alerts"] == 0
    assert future.status_code == 422
    log = db_session.scalar(select(AuditLog).where(AuditLog.action == "DETECT_ALERTS"))
    assert log is not None
    assert log.changes == {
        "date": [None, "2025-01-15"],
        "evaluated_meters": [None, 0],
        "created_alerts": [None, 0],
    }
