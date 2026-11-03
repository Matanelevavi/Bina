import json
from pathlib import Path
import pytest
from bina.sampling import stratified_sample, summarize, gps_leakage

SAMPLE = json.loads((Path(__file__).parent.parent / "data" / "sample.json").read_text())


def _pool():
    return [{"key": f"d/{c}{g}{i}", "class": c, "has_gps": g} for c in "ABC" for g in (True, False) for i in range(10)]


def test_quota_respected_and_deterministic():
    quota = {("A", True): 3, ("B", False): 2}
    s1 = stratified_sample(_pool(), quota, seed=1)
    s2 = stratified_sample(list(reversed(_pool())), quota, seed=1)
    assert summarize(s1) == quota and s1 == s2


def test_too_small_stratum_fails():
    with pytest.raises(ValueError):
        stratified_sample(_pool(), {("A", True): 11})


def test_committed_sample_matches_documented_design():
    assert len(SAMPLE) == 50 and len({f["key"] for f in SAMPLE}) == 50
    assert len({f["flight_date"] for f in SAMPLE}) == 37
    assert summarize(SAMPLE) == {
        ("Global Position", True): 12, ("External Position", True): 5,
        ("Normal", True): 4, ("Mechanical", True): 3,
        ("Altitude", False): 8, ("External Position", False): 6,
        ("Mechanical", False): 6, ("Normal", False): 6,
    }


def test_gps_leakage_visible_in_sample():
    leak = gps_leakage(SAMPLE)
    assert leak["Global Position"] == (12, 12)   # always GPS
    assert leak["Altitude"] == (0, 8)            # never GPS
