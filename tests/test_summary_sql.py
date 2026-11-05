import pytest
from bina.summary_sql import per_flight_summary_sql, BATTERY_SIGNALS, SENSOR_SIGNALS, _alias

FL = [("2019-03-19", "07_31_26"), ("2018-09-18", "08_51_40")]


def test_structure_and_quoting():
    sql = per_flight_summary_sql("sensor_combined", SENSOR_SIGNALS, FL)
    assert 'COUNT("gyro_rad[0]") AS gx_n' in sql
    assert "FROM bina_db.sensor_combined" in sql
    assert "GROUP BY flight_date, flight_id" in sql
    assert "IN ('2018-09-18', '2019-03-19')" in sql
    assert sql.count("starts_with(flight_id") == 2


def test_each_signal_has_five_aggregates():
    sql = per_flight_summary_sql("battery_status", BATTERY_SIGNALS, FL)
    for s in BATTERY_SIGNALS:
        for suffix in ("_n", "_min", "_max", "_avg", "_std"):
            assert f" AS {_alias(s)}{suffix}" in sql


@pytest.mark.parametrize("bad", [("2019-3-19", "07_31_26"), ("2019-03-19", "7_31_26"), ("x'; --", "07_31_26")])
def test_bad_reference_rejected(bad):
    with pytest.raises(ValueError):
        per_flight_summary_sql("battery_status", BATTERY_SIGNALS, [bad])


def test_empty_rejected():
    with pytest.raises(ValueError):
        per_flight_summary_sql("battery_status", BATTERY_SIGNALS, [])


from bina.summary_sql import summaries_from_row
from bina.features import build_prompt, mark_not_reported


def _row():
    return {"n_rows": "100", "gx_n": "100", "gx_min": "-1.5", "gx_max": "2.0", "gx_avg": "5.3E-4", "gx_std": "0.28",
            "alt_n": "0", "alt_min": "", "alt_max": "", "alt_avg": "", "alt_std": ""}


def test_parse_row_and_missing_signal():
    s = summaries_from_row(_row(), ["gyro_rad[0]", "baro_alt_meter"])
    assert s["gyro_rad[0]"]["max"] == 2.0 and s["gyro_rad[0]"]["n_missing"] == 0
    assert s["gyro_rad[0]"]["mean"] == pytest.approx(5.3e-4)
    assert s["baro_alt_meter"]["min"] is None and s["baro_alt_meter"]["n_missing"] == 100


def test_prompt_from_parsed_row():
    s = mark_not_reported(summaries_from_row(_row(), ["gyro_rad[0]", "baro_alt_meter"]))
    p = build_prompt(s, ["Normal", "Altitude"])
    assert "- gyro_rad[0]: min=-1.5, max=2" in p
    assert "- baro_alt_meter: n/a (no data)" in p


def test_instance_filter_present():
    sql = per_flight_summary_sql("battery_status", BATTERY_SIGNALS, FL)
    assert "AND ends_with(flight_id, '_0')" in sql
    assert "ends_with(flight_id, '_1')" in per_flight_summary_sql("battery_status", BATTERY_SIGNALS, FL, instance="1")


def test_date_with_trailing_dashes_accepted():
    sql = per_flight_summary_sql("battery_status", BATTERY_SIGNALS, [("2021-10-06--", "12_14_56")])
    assert "flight_date = '2021-10-06--'" in sql
