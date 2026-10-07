"""Schema-level checks: tables, delete rules, unique and CHECK constraints."""

from datetime import date

import pytest
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import AlertSeverity, AlertType
from app.models import Alert, ElectricityUsage
from tests.factories import create_meter, create_usage

EXPECTED_TABLES = {
    "users",
    "buildings",
    "floors",
    "rooms",
    "meters",
    "electricity_usages",
    "electricity_prices",
    "alerts",
}


def test_all_tables_exist(engine: Engine) -> None:
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES


def test_usage_indexes_exist(engine: Engine) -> None:
    inspector = inspect(engine)
    index_names = {index["name"] for index in inspector.get_indexes("electricity_usages")}
    unique_names = {uq["name"] for uq in inspector.get_unique_constraints("electricity_usages")}

    assert "ix_electricity_usages_recorded_at" in index_names
    assert "uq_electricity_usages_meter_id_recorded_at" in unique_names


def test_deleting_building_with_floors_is_restricted(db_session: Session) -> None:
    meter = create_meter(db_session)
    building = meter.room.floor.building

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.delete(building)
        db_session.flush()


def test_deleting_meter_cascades_usages_and_alerts(db_session: Session) -> None:
    meter = create_meter(db_session)
    create_usage(db_session, meter)
    db_session.add(
        Alert(
            meter_id=meter.id,
            alert_type=AlertType.HIGH_CONSUMPTION,
            severity=AlertSeverity.WARNING,
            message="Tiêu thụ cao bất thường",
            usage_date=date(2026, 10, 1),
        )
    )
    db_session.flush()
    meter_id = meter.id

    db_session.delete(meter)
    db_session.flush()

    usage_count = db_session.scalar(
        select(func.count())
        .select_from(ElectricityUsage)
        .where(ElectricityUsage.meter_id == meter_id)
    )
    alert_count = db_session.scalar(
        select(func.count()).select_from(Alert).where(Alert.meter_id == meter_id)
    )
    assert usage_count == 0
    assert alert_count == 0


def test_usage_is_unique_per_meter_and_hour(db_session: Session) -> None:
    meter = create_meter(db_session)
    first = create_usage(db_session, meter)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        create_usage(db_session, meter, recorded_at=first.recorded_at)


def test_meter_status_check_constraint(db_session: Session) -> None:
    meter = create_meter(db_session)

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE meters SET status = 'BROKEN' WHERE id = :id"), {"id": meter.id}
        )
