import pytest
from bina.paths import parse_raw_key, flight_id_from_filename


def test_depth_two_matched():
    k = parse_raw_key("2019-01-04/08_01_09_battery_status_0.csv")
    assert k.flight_date == "2019-01-04" and k.depth == 2 and k.matched_by_glob


def test_session_path_skipped_by_glob():
    k = parse_raw_key("2019-01-04/sess001/log001/08_01_09_battery_status_0.csv")
    assert k.depth == 4 and not k.matched_by_glob


def test_no_date_folder():
    assert not parse_raw_key("loose/file_battery_status_0.csv").matched_by_glob


def test_empty_key():
    with pytest.raises(ValueError):
        parse_raw_key("")


def test_flight_id():
    assert flight_id_from_filename("08_01_09_battery_status_0.csv") == "08_01_09_battery_status_0"
    with pytest.raises(ValueError):
        flight_id_from_filename("x.txt")
