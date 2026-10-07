from datetime import date, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import MeterStatus
from tests.factories import create_building, create_floor, create_meter, create_room, create_usage

URL = "/api/v1/meters"


def _payload(room_id: int, **overrides: Any) -> dict[str, Any]:
    return {
        "room_id": room_id,
        "meter_code": "m001",
        "name": "Công tơ phòng 101",
        "meter_type": "SINGLE_PHASE",
        **overrides,
    }


def test_manager_creates_meter_with_default_status(
    client: TestClient, db_session: Session, manager_headers: dict[str, str]
) -> None:
    room = create_room(db_session, code="R0101")

    response = client.post(URL, json=_payload(room.id), headers=manager_headers)

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["meter_code"] == "M001"
    assert data["status"] == "ACTIVE"
    assert data["room"]["code"] == "R0101"
    assert data["room"]["floor"]["building"]["code"] == "B01"


def test_create_meter_validation(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    room = create_room(db_session)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    bad_type = client.post(URL, json=_payload(room.id, meter_type="SOLAR"), headers=admin_headers)
    future_install = client.post(
        URL, json=_payload(room.id, installation_date=tomorrow), headers=admin_headers
    )
    unknown_room = client.post(URL, json=_payload(999999), headers=admin_headers)

    assert bad_type.status_code == 422
    assert bad_type.json()["error"]["details"][0]["field"] == "meter_type"
    assert future_install.json()["error"]["details"] == [
        {"field": "installation_date", "message": "Ngày lắp đặt không được ở tương lai"}
    ]
    assert unknown_room.json()["error"]["details"][0]["field"] == "room_id"


def test_meter_code_is_unique(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session, meter_code="M001")

    response = client.post(URL, json=_payload(meter.room_id), headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["error"]["details"][0]["field"] == "meter_code"


def test_list_meters_filters_by_floor_status_and_search(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    building = create_building(db_session)
    floor_1 = create_floor(db_session, building, floor_number=1)
    floor_2 = create_floor(db_session, building, floor_number=2)
    create_meter(db_session, create_room(db_session, floor_1, code="R1"), meter_code="M001")
    create_meter(
        db_session,
        create_room(db_session, floor_1, code="R2"),
        meter_code="M002",
        status=MeterStatus.MAINTENANCE,
    )
    create_meter(db_session, create_room(db_session, floor_2, code="R3"), meter_code="M003")

    def codes(**params: Any) -> list[str]:
        response = client.get(URL, params=params, headers=viewer_headers)
        return [item["meter_code"] for item in response.json()["data"]]

    assert codes(floor_id=floor_1.id) == ["M001", "M002"]
    assert codes(building_id=building.id, status="MAINTENANCE") == ["M002"]
    assert codes(search="m003") == ["M003"]


def test_delete_meter_removes_its_usages(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    meter = create_meter(db_session)
    create_usage(db_session, meter)

    response = client.delete(f"{URL}/{meter.id}", headers=admin_headers)

    assert response.status_code == 200
    usages = client.get(
        "/api/v1/electricity-usages", params={"meter_id": meter.id}, headers=admin_headers
    )
    assert usages.json()["pagination"]["total"] == 0
