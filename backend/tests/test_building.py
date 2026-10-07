from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_building, create_floor

URL = "/api/v1/buildings"

PAYLOAD: dict[str, Any] = {
    "name": "  EnergySmart Tower ",
    "code": "es-01",
    "address": "  ",
    "description": "Tòa nhà văn phòng",
}


def test_create_building_normalizes_input(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(URL, json=PAYLOAD, headers=admin_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Tạo tòa nhà thành công"
    data = body["data"]
    assert data["name"] == "EnergySmart Tower"
    assert data["code"] == "ES-01"
    assert data["address"] is None


def test_create_building_with_duplicate_code_returns_409(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    create_building(db_session, code="ES-01")

    response = client.post(URL, json=PAYLOAD, headers=admin_headers)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "CONFLICT"
    assert error["details"][0]["field"] == "code"


def test_create_building_validation_errors(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(URL, json={"name": "", "code": "mã sai!"}, headers=admin_headers)

    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["error"]["details"]}
    assert fields == {"name", "code"}


def test_list_buildings_paginates_sorts_and_searches(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    create_building(db_session, code="B01", name="Alpha Tower")
    create_building(db_session, code="B02", name="Beta Center")
    create_building(db_session, code="B03", name="Gamma Tower")

    page = client.get(URL, params={"page_size": 2}, headers=viewer_headers).json()
    assert [item["code"] for item in page["data"]] == ["B01", "B02"]
    assert page["pagination"] == {"page": 1, "page_size": 2, "total": 3, "total_pages": 2}

    searched = client.get(
        URL,
        params={"search": "tower", "sort_by": "name", "sort_order": "desc"},
        headers=viewer_headers,
    ).json()
    assert [item["name"] for item in searched["data"]] == ["Gamma Tower", "Alpha Tower"]


def test_search_treats_wildcards_literally(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    create_building(db_session, code="B01")

    response = client.get(URL, params={"search": "%"}, headers=viewer_headers)

    assert response.json()["pagination"]["total"] == 0


def test_list_rejects_unknown_sort_field(
    client: TestClient, viewer_headers: dict[str, str]
) -> None:
    response = client.get(URL, params={"sort_by": "password"}, headers=viewer_headers)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "sort_by"


def test_get_building_not_found(client: TestClient, viewer_headers: dict[str, str]) -> None:
    response = client.get(f"{URL}/999999", headers=viewer_headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Không tìm thấy tòa nhà có id=999999"


def test_update_building_keeping_its_own_code(
    client: TestClient, db_session: Session, manager_headers: dict[str, str]
) -> None:
    building = create_building(db_session, code="ES-01")

    response = client.put(
        f"{URL}/{building.id}", json={**PAYLOAD, "name": "Tòa nhà mới"}, headers=manager_headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Tòa nhà mới"
    assert response.json()["data"]["code"] == "ES-01"


def test_delete_building_with_floors_returns_409(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    building = create_building(db_session)
    create_floor(db_session, building)

    response = client.delete(f"{URL}/{building.id}", headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["message"] == "Không thể xóa tòa nhà đang có 1 tầng"


def test_delete_building(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    building = create_building(db_session)

    response = client.delete(f"{URL}/{building.id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Xóa tòa nhà thành công",
        "data": None,
    }
    assert client.get(f"{URL}/{building.id}", headers=admin_headers).status_code == 404


def test_viewer_cannot_modify_buildings(client: TestClient, viewer_headers: dict[str, str]) -> None:
    response = client.post(URL, json=PAYLOAD, headers=viewer_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_listing_requires_authentication(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
