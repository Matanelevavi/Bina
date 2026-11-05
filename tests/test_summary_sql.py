import pytest
from bina.summary_sql import per_flight_summary_sql, BATTERY_SIGNALS, SENSOR_SIGNALS

FL = [("2019-03-19", "07_31_26"), ("2018-09-18", "08_51_40")]


def test_structure_and_quoting():
    sql = per_flight_summary_sql("sensor_combined", SENSOR_SIGNALS, FL)
    assert 'COUNT("gyro_rad[0]") AS gyro_rad_0_n' in sql
    assert "FROM bina_db.sensor_combined" in sql
    assert "GROUP BY flight_date, flight_id" in sql
    assert "IN ('2018-09-18', '2019-03-19')" in sql
    assert sql.count("starts_with(flight_id") == 2


def test_each_signal_has_five_aggregates():
    sql = per_flight_summary_sql("battery_status", BATTERY_SIGNALS, FL)
    for s in BATTERY_SIGNALS:
        for suffix in ("_n", "_min", "_max", "_avg", "_std"):
            assert f" AS {s}{suffix}" in sql


@pytest.mark.parametrize("bad", [("2019-3-19", "07_31_26"), ("2019-03-19", "7_31_26"), ("x'; --", "07_31_26")])
def test_bad_reference_rejected(bad):
    with pytest.raises(ValueError):
        per_flight_summary_sql("battery_status", BATTERY_SIGNALS, [bad])


def test_empty_rejected():
    with pytest.raises(ValueError):
        per_flight_summary_sql("battery_status", BATTERY_SIGNALS, [])
