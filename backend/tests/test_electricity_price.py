from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_price

URL = "/api/v1/electricity-prices"


def test_admin_creates_price(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        URL,
        json={"name": "Giá 2026", "price_per_kwh": 2100.5, "effective_from": "2026-01-01"},
        headers=admin_headers,
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["price_per_kwh"] == 2100.5
    assert data["effective_to"] is None


def test_manager_cannot_write_prices(client: TestClient, manager_headers: dict[str, str]) -> None:
    response = client.post(
        URL,
        json={"name": "Giá", "price_per_kwh": 2000, "effective_from": "2026-01-01"},
        headers=manager_headers,
    )

    assert response.status_code == 403


def test_overlapping_periods_are_rejected(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    create_price(db_session, effective_from=date(2025, 1, 1), effective_to=date(2025, 12, 31))

    overlapping = client.post(
        URL,
        json={"name": "Mới", "price_per_kwh": 2200, "effective_from": "2025-12-01"},
        headers=admin_headers,
    )
    adjacent = client.post(
        URL,
        json={"name": "Mới", "price_per_kwh": 2200, "effective_from": "2026-01-01"},
        headers=admin_headers,
    )

    assert overlapping.status_code == 409
    assert overlapping.json()["error"]["details"][0]["field"] == "effective_from"
    assert adjacent.status_code == 201


def test_invalid_period_returns_422(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        URL,
        json={
            "name": "Sai",
            "price_per_kwh": 2000,
            "effective_from": "2026-02-01",
            "effective_to": "2026-01-01",
        },
        headers=admin_headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["message"] == (
        "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu hiệu lực"
    )


def test_update_price_does_not_conflict_with_itself(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    price = create_price(db_session, Decimal("2000.00"), date(2025, 1, 1))

    response = client.put(
        f"{URL}/{price.id}",
        json={"name": "Điều chỉnh", "price_per_kwh": 2050, "effective_from": "2025-01-01"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["price_per_kwh"] == 2050.0


def test_list_prices_active_on(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    create_price(db_session, Decimal("2000.00"), date(2024, 1, 1), date(2024, 12, 31), "2024")
    create_price(db_session, Decimal("2100.00"), date(2025, 1, 1), None, "2025")

    all_prices = client.get(URL, headers=viewer_headers).json()["data"]
    active = client.get(URL, params={"active_on": "2024-06-15"}, headers=viewer_headers).json()

    assert [item["name"] for item in all_prices] == ["2025", "2024"]
    assert [item["name"] for item in active["data"]] == ["2024"]
