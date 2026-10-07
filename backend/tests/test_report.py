from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.report import ConsumptionReportParams
from app.services.report_service import ReportService
from tests.analytics_fixtures import NOW, add_usage, build_two_floors, local


def _report(db: Session, group_by: str) -> list[tuple[str, str, str, float]]:
    report = ReportService(db, now=lambda: NOW).consumption(
        ConsumptionReportParams.model_validate({"group_by": group_by})
    )
    return [(row.code, row.name, row.parent, row.share_percent) for row in report.rows]


def test_report_defaults_to_current_month_and_groups(db_session: Session) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "1.000")
    add_usage(db_session, data.meter_b, local(3, 9), "3.000")
    add_usage(db_session, data.meter_b, local(20, 9, month=5), "50.000")  # previous month

    report = ReportService(db_session, now=lambda: NOW).consumption(ConsumptionReportParams())

    assert (report.from_date, report.to_date) == (date(2025, 6, 1), date(2025, 6, 4))
    assert report.total_kwh == Decimal("4.000")
    assert report.total_cost == Decimal("4.000") * 2500
    assert _report(db_session, "floor") == [("1", "Tầng 1", "", 25.0), ("2", "Tầng 2", "", 75.0)]
    assert _report(db_session, "room") == [
        ("R0201", "Phòng B", "Tầng 2", 75.0),
        ("R0101", "Phòng A", "Tầng 1", 25.0),
    ]
    assert [code for code, *_ in _report(db_session, "meter")] == ["MB", "MA"]


def test_csv_export(
    client: TestClient, db_session: Session, viewer_headers: dict[str, str]
) -> None:
    data = build_two_floors(db_session)
    add_usage(db_session, data.meter_a, local(2, 9), "1.500")

    response = client.get(
        "/api/v1/reports/consumption/export",
        params={"group_by": "room", "from_date": "2025-06-01", "to_date": "2025-06-30"},
        headers=viewer_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="bao-cao-dien-nang_phong_20250601-20250630.csv"'
    )
    text = response.content.decode("utf-8")
    assert text.startswith(chr(0xFEFF))
    lines = text.lstrip(chr(0xFEFF)).splitlines()
    assert lines[0] == "Mã,Tên,Thuộc,Điện năng (kWh),Chi phí (VND),Tỷ trọng (%)"
    assert lines[1] == "R0101,Phòng A,Tầng 1,1.500,3750,100.0"
    assert lines[-1] == ",Tổng cộng,,1.500,3750,100"


def test_report_endpoint_rejects_unknown_group(
    client: TestClient, viewer_headers: dict[str, str]
) -> None:
    response = client.get(
        "/api/v1/reports/consumption", params={"group_by": "city"}, headers=viewer_headers
    )

    assert response.status_code == 422
