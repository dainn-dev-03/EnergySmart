from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_building, create_floor, create_room

URL = "/api/v1/floors"


def test_create_floor_returns_building_reference(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    building = create_building(db_session, code="ES-01", name="EnergySmart Tower")

    response = client.post(
        URL,
        json={"building_id": building.id, "name": "Tầng 3", "floor_number": 3},
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["floor_number"] == 3
    assert data["building"] == {"id": building.id, "name": "EnergySmart Tower", "code": "ES-01"}


def test_create_floor_with_unknown_building_returns_422(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(
        URL,
        json={"building_id": 999999, "name": "Tầng 1", "floor_number": 1},
        headers=admin_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"field": "building_id", "message": "Tòa nhà không tồn tại"}
    ]


def test_floor_number_is_unique_per_building(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    building_a = create_building(db_session, code="A")
    building_b = create_building(db_session, code="B")
    create_floor(db_session, building_a, floor_number=1)

    duplicate = client.post(
        URL,
        json={"building_id": building_a.id, "name": "T1", "floor_number": 1},
        headers=admin_headers,
    )
    other_building = client.post(
        URL,
        json={"building_id": building_b.id, "name": "T1", "floor_number": 1},
        headers=admin_headers,
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["details"][0]["field"] == "floor_number"
    assert other_building.status_code == 201


def test_list_floors_filters_by_building(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    building_a = create_building(db_session, code="A")
    building_b = create_building(db_session, code="B")
    create_floor(db_session, building_a, floor_number=2)
    create_floor(db_session, building_a, floor_number=1)
    create_floor(db_session, building_b, floor_number=1)

    response = client.get(URL, params={"building_id": building_a.id}, headers=viewer_headers)

    assert [item["floor_number"] for item in response.json()["data"]] == [1, 2]


def test_update_floor_moves_it_to_another_building(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    floor = create_floor(db_session, create_building(db_session, code="A"))
    target = create_building(db_session, code="B")

    response = client.put(
        f"{URL}/{floor.id}",
        json={"building_id": target.id, "name": "Tầng 1", "floor_number": 1},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["building_id"] == target.id
    assert data["building"]["code"] == "B"


def test_delete_floor_with_rooms_returns_409(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    floor = create_floor(db_session)
    create_room(db_session, floor)

    response = client.delete(f"{URL}/{floor.id}", headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["message"] == "Không thể xóa tầng đang có 1 phòng"
