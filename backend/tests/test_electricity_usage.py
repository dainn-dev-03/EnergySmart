from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import (
    create_building,
    create_floor,
    create_meter,
    create_price,
    create_room,
    create_usage,
)

URL = "/api/v1/electricity-usages"


def _payload(meter_id: int, **overrides: Any) -> dict[str, Any]:
    return {
        "meter_id": meter_id,
        "recorded_at": "2025-06-01T08:00:00+07:00",
        "kwh": 1.25,
        "voltage": 220.5,
        "current": 6.12,
        "power_factor": 0.93,
        **overrides,
    }


def test_create_usage_calculates_cost_from_price(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_price(db_session, Decimal("2000.00"), date(2020, 1, 1), date(2025, 5, 31), "Cũ")
    create_price(db_session, Decimal("2500.00"), date(2025, 6, 1), None, "Mới")

    response = client.post(URL, json=_payload(meter.id), headers=admin_headers)

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["kwh"] == 1.25
    assert data["cost"] == 3125.0  # 1.25 kWh × 2,500 VND (price valid on 2025-06-01)
    assert data["recorded_at"] == "2025-06-01T01:00:00Z"
    assert data["meter"]["meter_code"] == "M001"


def test_naive_datetime_is_interpreted_as_vietnam_time(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_price(db_session)

    response = client.post(
        URL, json=_payload(meter.id, recorded_at="2025-06-01T08:00:00"), headers=admin_headers
    )

    assert response.json()["data"]["recorded_at"] == "2025-06-01T01:00:00Z"


def test_create_usage_without_price_returns_price_not_found(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)

    response = client.post(URL, json=_payload(meter.id), headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "PRICE_NOT_FOUND"
    assert body["message"] == "Chưa có bảng giá điện áp dụng cho ngày 2025-06-01"


def test_create_usage_validation(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_price(db_session)
    next_hour = (datetime.now(UTC) + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

    def first_error(**overrides: Any) -> dict[str, Any]:
        response = client.post(URL, json=_payload(meter.id, **overrides), headers=admin_headers)
        assert response.status_code == 422
        detail: dict[str, Any] = response.json()["error"]["details"][0]
        return detail

    assert first_error(recorded_at="2025-06-01T08:30:00+07:00") == {
        "field": "recorded_at",
        "message": "Thời điểm ghi phải là đầu giờ (phút và giây bằng 0)",
    }
    assert first_error(recorded_at=next_hour.isoformat())["message"] == (
        "Không thể ghi nhận dữ liệu ở thời điểm tương lai"
    )
    assert first_error(kwh=-1)["field"] == "kwh"
    assert first_error(power_factor=1.5)["field"] == "power_factor"
    assert first_error(meter_id=999999) == {"field": "meter_id", "message": "Công tơ không tồn tại"}


def test_duplicate_reading_returns_409(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_price(db_session)
    create_usage(db_session, meter, recorded_at=datetime(2025, 6, 1, 1, tzinfo=UTC))

    response = client.post(URL, json=_payload(meter.id), headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["error"]["details"][0]["field"] == "recorded_at"


def test_list_usages_filters_by_hierarchy_and_local_dates(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    floor_a = create_floor(db_session, create_building(db_session, code="A"))
    floor_b = create_floor(db_session, create_building(db_session, code="B"))
    meter_a = create_meter(db_session, create_room(db_session, floor_a, code="RA"), "MA")
    meter_b = create_meter(db_session, create_room(db_session, floor_b, code="RB"), "MB")
    # 2025-05-31 23:00 and 2025-06-01 00:00 in Vietnam (UTC+7).
    late_may_31 = create_usage(db_session, meter_a, datetime(2025, 5, 31, 16, tzinfo=UTC))
    create_usage(db_session, meter_a, datetime(2025, 5, 31, 17, tzinfo=UTC))
    create_usage(db_session, meter_b, datetime(2025, 5, 31, 16, tzinfo=UTC))

    response = client.get(
        URL,
        params={
            "building_id": floor_a.building_id,
            "from_date": "2025-05-31",
            "to_date": "2025-05-31",
        },
        headers=viewer_headers,
    )

    assert [item["id"] for item in response.json()["data"]] == [late_may_31.id]


def test_list_usages_sorted_newest_first_and_rejects_bad_range(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    older = create_usage(db_session, meter, datetime(2025, 6, 1, 1, tzinfo=UTC))
    newer = create_usage(db_session, meter, datetime(2025, 6, 1, 2, tzinfo=UTC))

    listed = client.get(URL, headers=viewer_headers).json()["data"]
    bad_range = client.get(
        URL, params={"from_date": "2025-06-02", "to_date": "2025-06-01"}, headers=viewer_headers
    )

    assert [item["id"] for item in listed] == [newer.id, older.id]
    assert bad_range.status_code == 422


def test_update_usage_recalculates_cost(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_price(db_session, Decimal("2000.00"))
    usage = create_usage(db_session, meter, datetime(2025, 6, 1, 1, tzinfo=UTC))

    response = client.put(
        f"{URL}/{usage.id}", json=_payload(meter.id, kwh=2), headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["cost"] == 4000.0


def test_viewer_cannot_create_usage(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)

    response = client.post(URL, json=_payload(meter.id), headers=viewer_headers)

    assert response.status_code == 403
