import pytest
from bina.sqlgen import where_clause, count_and_avg

PAIRS = [("2019-01-07", "b_battery_status_0"), ("2018-06-04", "a_battery_status_0"),
         ("2018-06-04", "c_battery_status_0"), ("2018-06-04", "a_battery_status_0")]


def test_dates_deduplicated_and_sorted():
    w = where_clause(PAIRS)
    assert "IN ('2018-06-04', '2019-01-07')" in w


def test_pairs_deduplicated():
    assert where_clause(PAIRS).count("flight_id =") == 3


def test_empty_rejected():
    with pytest.raises(ValueError):
        where_clause([])


def test_quote_rejected():
    with pytest.raises(ValueError):
        where_clause([("2019-01-01", "x'; DROP")])


def test_count_and_avg():
    c, a = count_and_avg("bina_db.battery_status", "voltage_v", PAIRS)
    assert c.startswith("SELECT COUNT(DISTINCT flight_id)")
    assert "AVG(voltage_v) AS avg_voltage_v" in a
