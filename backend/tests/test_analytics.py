from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidInputError
from app.schemas.analytics import ComparisonParams, DateRangeParams, RoomBreakdownParams
from app.services.analytics_service import AnalyticsService, percentage_change
from tests.analytics_fixtures import NOW, add_usage, build_two_floors, local


def _service(db: Session) -> AnalyticsService:
    return AnalyticsService(db, now=lambda: NOW)


def test_percentage_change_formula() -> None:
    assert percentage_change(Decimal(125), Decimal(100)) == 25.0
    assert percentage_change(Decimal(80), Decimal(100)) == -20.0
    assert percentage_change(Decimal(5), Decimal(0)) is None


def test_daily_filters_by_floor(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "1.000")
    add_usage(db_session, data.meter_b, local(2, 9), "9.000")

    points = _service(db_session).daily(
        DateRangeParams(
            floor_id=data.floor_1.id, from_date=date(2025, 6, 2), to_date=date(2025, 6, 3)
        )
    )

    assert [(point.date, point.kwh) for point in points] == [
        (date(2025, 6, 2), Decimal("1.000")),
        (date(2025, 6, 3), 0),
    ]


def test_hourly_profile_averages_weekdays_and_weekends(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "2.000")  # Monday
    add_usage(db_session, data.meter_a, local(3, 9), "4.000")  # Tuesday
    add_usage(db_session, data.meter_a, local(1, 9), "1.000")  # Sunday

    points = _service(db_session).hourly(
        DateRangeParams(from_date=date(2025, 6, 1), to_date=date(2025, 6, 3))
    )

    assert (points[9].weekday_kwh, points[9].weekend_kwh) == (Decimal("3.000"), Decimal("1.000"))
    assert len(points) == 24
    assert points[0].weekday_kwh == 0


def test_by_floor_and_by_room_shares(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "1.000")
    add_usage(db_session, data.meter_b, local(2, 9), "3.000")
    first, last = date(2025, 6, 1), date(2025, 6, 4)

    floors = _service(db_session).by_floor(DateRangeParams(from_date=first, to_date=last))
    rooms = _service(db_session).by_room(RoomBreakdownParams(from_date=first, to_date=last))

    assert [(f.floor_number, f.share_percent) for f in floors] == [(1, 25.0), (2, 75.0)]
    assert [(r.room_code, r.floor_name) for r in rooms] == [
        ("R0201", "Tầng 2"),
        ("R0101", "Tầng 1"),
    ]


def test_month_comparison_uses_same_elapsed_time(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "10.000")  # current: June 1 -> June 4 10:30
    add_usage(
        db_session, data.meter_a, local(3, 9, month=5), "8.000"
    )  # previous: May 1 -> May 4 10:30
    add_usage(db_session, data.meter_a, local(20, 9, month=5), "100.000")  # outside the window

    result = _service(db_session).comparison(ComparisonParams(period="month"))

    assert result.current_period.kwh == Decimal("10.000")
    assert result.previous_period.kwh == Decimal("8.000")
    assert result.previous_period.end == local(4, 10, month=5).replace(minute=30)
    assert result.difference == Decimal("2.000")
    assert result.percentage_change == 25.0


def test_custom_comparison_with_empty_previous_period(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "3.000")

    result = _service(db_session).comparison(
        ComparisonParams(current_from=date(2025, 6, 2), current_to=date(2025, 6, 3))
    )

    assert result.period == "custom"
    assert result.previous_period.start == local(31, 0, month=5)
    assert result.percentage_change is None


def test_comparison_of_future_period_is_rejected(db_session: Session) -> None:
    with pytest.raises(InvalidInputError):
        _service(db_session).comparison(
            ComparisonParams(period="day", reference_date=date(2025, 6, 10))
        )


def test_analytics_endpoints_validate_input(
    client: TestClient, viewer_headers: dict[str, str]
) -> None:
    bad_range = client.get(
        "/api/v1/analytics/daily",
        params={"from_date": "2025-06-05", "to_date": "2025-06-01"},
        headers=viewer_headers,
    )
    half_custom = client.get(
        "/api/v1/analytics/comparison",
        params={"current_from": "2025-06-01"},
        headers=viewer_headers,
    )

    assert bad_range.status_code == 422
    assert half_custom.status_code == 422


def test_analytics_endpoints_respond(client: TestClient, viewer_headers: dict[str, str]) -> None:
    for path in ("daily", "monthly", "hourly", "by-floor", "by-room", "comparison"):
        response = client.get(f"/api/v1/analytics/{path}", headers=viewer_headers)
        assert response.status_code == 200, path

    comparison = client.get("/api/v1/analytics/comparison", headers=viewer_headers).json()["data"]
    assert set(comparison) >= {
        "current_period",
        "previous_period",
        "difference",
        "percentage_change",
    }
