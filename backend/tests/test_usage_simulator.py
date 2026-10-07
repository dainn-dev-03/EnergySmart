from dataclasses import replace
from datetime import date, timedelta
from statistics import mean

from app.core.enums import MeterStatus
from app.seed.master_data import TARGET_WEEKDAY_KWH, meter_specs
from app.seed.usage_simulator import DemoScenario, MeterLoad, UsageSimulator

TODAY = date(2025, 6, 4)  # a Wednesday
SCENARIO = DemoScenario(today=TODAY, random_anomaly_probability=0.0, forced_anomalies=())


def _load(meter_code: str) -> MeterLoad:
    return meter_specs()[meter_code].load


def _daily_kwh(simulator: UsageSimulator, meter: MeterLoad, day: date) -> float:
    return sum(reading.kwh for reading in simulator.day_readings(meter, day))


def test_layout_has_50_meters_with_expected_statuses() -> None:
    specs = meter_specs()
    statuses = [spec.load.status for spec in specs.values()]

    assert len(specs) == 50
    assert statuses.count(MeterStatus.ACTIVE) == 46
    assert statuses.count(MeterStatus.INACTIVE) == 2
    assert statuses.count(MeterStatus.MAINTENANCE) == 2
    assert specs["M001"].room_code == "R0101"
    assert specs["M050"].room_code == "R1005"


def test_peak_loads_are_calibrated_to_target_weekday_consumption() -> None:
    expected_weekday_kwh = sum(
        spec.load.peak_kw * spec.load.profile.weekday_peak_hours
        for spec in meter_specs().values()
        if spec.load.status is MeterStatus.ACTIVE
    )

    assert abs(expected_weekday_kwh - TARGET_WEEKDAY_KWH) < 1


def test_readings_are_deterministic() -> None:
    meter = _load("M006")

    first = UsageSimulator(SCENARIO, random_seed=42).day_readings(meter, TODAY)
    second = UsageSimulator(SCENARIO, random_seed=42).day_readings(meter, TODAY)
    other_seed = UsageSimulator(SCENARIO, random_seed=7).day_readings(meter, TODAY)

    assert first == second
    assert first != other_seed


def test_office_peaks_during_working_hours() -> None:
    readings = UsageSimulator(SCENARIO, 42).day_readings(_load("M006"), TODAY)

    peak = mean(readings[hour].kwh for hour in (9, 10, 14, 15))
    night = mean(readings[hour].kwh for hour in range(0, 5))
    lunch = readings[12].kwh

    assert peak > 5 * night
    assert night < lunch < peak


def test_weekends_consume_less_than_weekdays() -> None:
    simulator = UsageSimulator(SCENARIO, 42)
    meter = _load("M006")
    days = [TODAY - timedelta(days=offset) for offset in range(28)]

    weekday = mean(_daily_kwh(simulator, meter, day) for day in days if day.weekday() < 5)
    sunday = mean(_daily_kwh(simulator, meter, day) for day in days if day.weekday() == 6)

    assert sunday < 0.5 * weekday


def test_forced_anomaly_and_floor_event() -> None:
    normal = UsageSimulator(SCENARIO, 42)
    demo = UsageSimulator(DemoScenario(today=TODAY, random_anomaly_probability=0.0), 42)
    yesterday = TODAY - timedelta(days=1)
    m003 = _load("M003")
    floor_3_meter = _load("M011")

    anomaly_ratio = _daily_kwh(demo, m003, yesterday) / _daily_kwh(normal, m003, yesterday)
    floor_ratio = _daily_kwh(demo, floor_3_meter, yesterday) / _daily_kwh(
        UsageSimulator(replace(SCENARIO, floor_event_factor=1.0), 42), floor_3_meter, yesterday
    )

    assert abs(anomaly_ratio - 2.3) < 0.01
    assert abs(floor_ratio - 1.25) < 0.01


def test_inactive_and_maintenance_meters_stop_reporting() -> None:
    inactive = _load("M024")
    maintenance = _load("M020")

    assert SCENARIO.has_data(inactive, TODAY - timedelta(days=30))
    assert not SCENARIO.has_data(inactive, TODAY - timedelta(days=29))
    assert SCENARIO.has_data(maintenance, TODAY - timedelta(days=2))
    assert not SCENARIO.has_data(maintenance, TODAY - timedelta(days=1))
