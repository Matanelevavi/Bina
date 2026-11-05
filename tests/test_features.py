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


def test_constant_zero_temperature_is_not_reported():
    p = build_prompt(summarize_flight(_rows(temperature=[0.0, 0.0, 0.0])), LABELS)
    assert "temperature: n/a (not reported)" in p


def test_zero_rule_only_for_listed_signals():
    p = build_prompt(summarize_flight(_rows(current_a=[0.0, 0.0])), LABELS)
    assert "current_a: min=0, max=0" in p


def test_real_temperature_kept():
    p = build_prompt(summarize_flight(_rows(temperature=[0.0, 25.0])), LABELS)
    assert "temperature: min=0, max=25" in p


def test_delta_not_a_signal():
    assert "max_cell_voltage_delta" not in SIGNALS


def test_source_description_in_prompt():
    summ = summarize_flight(_rows())
    assert "(battery telemetry)" in build_prompt(summ, LABELS)
    assert "(battery and motion-sensor telemetry)" in build_prompt(summ, LABELS, "battery and motion-sensor telemetry")
