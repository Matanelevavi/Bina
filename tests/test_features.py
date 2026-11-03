import math
import pytest
from bina.features import SIGNALS, summarize_signal, summarize_flight, build_prompt

LABELS = ["Normal", "Altitude"]


def test_stats_ignore_missing_but_count_them():
    s = summarize_signal([1.0, None, 3.0, float("nan")])
    assert (s["n_total"], s["n_missing"]) == (4, 2)
    assert (s["min"], s["max"], s["mean"]) == (1.0, 3.0, 2.0)
    assert s["std"] == pytest.approx(1.0)


def test_all_missing_is_none_not_zero():
    s = summarize_signal([None, None])
    assert s["mean"] is None and s["n_missing"] == 2


def _rows(**over):
    r = {k: [1.0, 2.0] for k in SIGNALS}
    r.update(over)
    return r


def test_missing_signal_key_raises():
    r = _rows(); del r["scale"]
    with pytest.raises(KeyError):
        summarize_flight(r)


def test_prompt_marks_no_data_and_partial_gaps():
    p = build_prompt(summarize_flight(_rows(temperature=[None, None], scale=[1.0, None])), LABELS)
    assert "temperature: n/a (no data)" in p
    assert "1 of 2 values missing" in p
    assert "Normal, Altitude" in p


def test_prompt_has_no_identifiers():
    p = build_prompt(summarize_flight(_rows()), LABELS)
    assert "flight_date" not in p and "flight_id" not in p
