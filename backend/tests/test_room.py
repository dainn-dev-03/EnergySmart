from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_building, create_floor, create_meter, create_room

URL = "/api/v1/rooms"


def test_create_room_returns_area_as_number_and_parents(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    floor = create_floor(db_session, create_building(db_session, code="ES-01"), floor_number=3)

    response = client.post(
        URL,
        json={"floor_id": floor.id, "name": "Phòng họp", "code": "r0301", "area": 65.5},
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["code"] == "R0301"
    assert data["area"] == 65.5
    assert data["floor"]["floor_number"] == 3
    assert data["floor"]["building"]["code"] == "ES-01"


def test_create_room_rejects_unknown_floor_and_bad_area(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    unknown_floor = client.post(
        URL, json={"floor_id": 999999, "name": "P", "code": "R1"}, headers=admin_headers
    )
    bad_area = client.post(
        URL, json={"floor_id": 1, "name": "P", "code": "R1", "area": 10.555}, headers=admin_headers
    )

    assert unknown_floor.status_code == 422
    assert unknown_floor.json()["error"]["details"][0]["field"] == "floor_id"
    assert bad_area.status_code == 422
    assert bad_area.json()["error"]["details"] == [
        {"field": "area", "message": "Tối đa 2 chữ số thập phân"}
    ]


def test_room_code_is_unique(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    room = create_room(db_session, code="R0101")

    response = client.post(
        URL, json={"floor_id": room.floor_id, "name": "P", "code": "R0101"}, headers=admin_headers
    )

    assert response.status_code == 409


def test_list_rooms_filters_by_building(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    floor_a = create_floor(db_session, create_building(db_session, code="A"))
    floor_b = create_floor(db_session, create_building(db_session, code="B"))
    create_room(db_session, floor_a, code="A-101")
    create_room(db_session, floor_b, code="B-101")

    response = client.get(URL, params={"building_id": floor_a.building_id}, headers=viewer_headers)

    assert [item["code"] for item in response.json()["data"]] == ["A-101"]


def test_delete_room_with_meter_returns_409_then_succeeds_when_empty(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    occupied = create_room(db_session, code="R1")
    create_meter(db_session, occupied)
    empty = create_room(db_session, occupied.floor, code="R2")

    assert client.delete(f"{URL}/{occupied.id}", headers=admin_headers).status_code == 409
    assert client.delete(f"{URL}/{empty.id}", headers=admin_headers).status_code == 200
