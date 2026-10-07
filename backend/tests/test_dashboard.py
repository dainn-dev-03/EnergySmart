from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import AlertSeverity, AlertType, MeterStatus
from app.models import Alert
from app.services.dashboard_service import DashboardService
from tests.analytics_fixtures import NOW, add_usage, build_two_floors, local
from tests.factories import create_meter, create_room


def _service(db: Session) -> DashboardService:
    return DashboardService(db, now=lambda: NOW)


def test_summary_counts_today_month_meters_and_open_alerts(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(4, 8), "2.000")  # today
    add_usage(db_session, data.meter_b, local(4, 0), "3.000")  # today, first hour (17:00 UTC)
    add_usage(db_session, data.meter_a, local(1, 9), "1.000")  # this month
    add_usage(db_session, data.meter_a, local(31, 23, month=5), "5.000")  # last month
    create_meter(
        db_session,
        create_room(db_session, data.floor_1, code="R0102"),
        "MC",
        status=MeterStatus.MAINTENANCE,
    )
    for resolved in (False, True):
        db_session.add(
            Alert(
                meter_id=data.meter_a.id,
                alert_type=AlertType.HIGH_CONSUMPTION,
                severity=AlertSeverity.WARNING,
                message="Tiêu thụ cao",
                usage_date=date(2025, 6, 1) + timedelta(days=int(resolved)),
                is_resolved=resolved,
            )
        )
    db_session.flush()

    summary = _service(db_session).summary(building_id=None)

    assert summary.today_kwh == Decimal("5.000")
    assert summary.month_kwh == Decimal("6.000")
    assert summary.month_cost == Decimal("6.000") * 2500
    assert summary.active_meters == 2
    assert summary.alert_count == 1


def test_daily_series_is_zero_filled_in_local_days(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 23), "4.000")  # 16:00 UTC, still June 2 locally

    points = _service(db_session).daily(days=3, building_id=None)

    assert [(point.date.day, float(point.kwh)) for point in points] == [(2, 4), (3, 0), (4, 0)]


def test_monthly_series_covers_each_month(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(15, 9, month=4), "7.000")
    add_usage(db_session, data.meter_a, local(2, 9), "1.500")

    points = _service(db_session).monthly(months=3, building_id=None)

    assert [(point.month, point.kwh) for point in points] == [
        ("2025-04", 7),
        ("2025-05", 0),
        ("2025-06", Decimal("1.5")),
    ]


def test_floor_trends_flag_increase_of_20_percent(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(1, 9), "12.000")  # last 7 days
    add_usage(db_session, data.meter_a, local(25, 9, month=5), "10.000")  # 7-14 days ago
    add_usage(db_session, data.meter_b, local(1, 9), "9.000")
    add_usage(db_session, data.meter_b, local(25, 9, month=5), "10.000")

    trends = _service(db_session).floor_trends(building_id=None)

    assert [(t.floor_number, t.percentage_change, t.status) for t in trends] == [
        (1, 20.0, "WARNING"),
        (2, -10.0, "NORMAL"),
    ]


def test_top_rooms_this_month(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "1.000")
    add_usage(db_session, data.meter_b, local(2, 9), "3.000")

    rooms = _service(db_session).top_rooms(limit=1, building_id=None)

    assert [(room.room_code, room.share_percent) for room in rooms] == [("R0201", 75.0)]


def test_dashboard_endpoints_return_envelopes(
    client: TestClient, viewer_headers: dict[str, str]
) -> None:
    for path in ("summary", "daily", "monthly", "by-floor", "by-room", "cost"):
        response = client.get(f"/api/v1/dashboard/{path}", headers=viewer_headers)
        assert response.status_code == 200, path
        assert response.json()["success"] is True

    summary = client.get("/api/v1/dashboard/summary", headers=viewer_headers).json()["data"]
    assert set(summary) == {"today_kwh", "month_kwh", "month_cost", "active_meters", "alert_count"}
    daily = client.get("/api/v1/dashboard/daily", params={"days": 7}, headers=viewer_headers)
    assert len(daily.json()["data"]) == 7


def test_dashboard_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/dashboard/summary").status_code == 401
