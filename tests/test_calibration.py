import pytest
from bina.calibration import pick_calibration


def f(key, cls, gps):
    return {"key": key, "flight_date": key.split("/")[0], "flight": key.split("/")[1], "class": cls, "has_gps": gps}


SAMPLE = [f("2019-01-01/a", "Normal", False)]
POOL = SAMPLE + [f("2019-01-01/b", "Normal", False), f("2019-02-02/c", "Normal", False),
                 f("2019-01-01/d", "Global Position", True)]


def test_never_picks_sample_flight():
    for seed in range(20):
        r = pick_calibration(POOL, SAMPLE, [("Normal", False)], seed=seed)
        assert r[0]["key"] != "2019-01-01/a"


def test_prefers_dates_outside_sample():
    r = pick_calibration(POOL, SAMPLE, [("Normal", False)])
    assert r[0]["key"] == "2019-02-02/c" and not r[0]["same_date_as_sample"]


def test_relaxation_is_reported():
    r = pick_calibration(POOL, SAMPLE, [("Global Position", True)])
    assert r[0]["same_date_as_sample"] is True


def test_empty_stratum_raises():
    with pytest.raises(ValueError):
        pick_calibration(POOL, SAMPLE, [("Altitude", False)])


def test_deterministic():
    a = pick_calibration(POOL, SAMPLE, [("Normal", False)], seed=3)
    assert a == pick_calibration(list(reversed(POOL)), SAMPLE, [("Normal", False)], seed=3)
