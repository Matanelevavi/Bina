"""Per-flight feature summary and prompt construction for the Bedrock classifier.

Design decisions (see docs/evaluation-design.md):
- Raw rows are never sent: flights range from 52 to 1,029 rows, so each signal is reduced to min/max/mean/std.
- Statistics use only non-missing values. The number of missing values is kept, so partial gaps stay visible.
- A signal with no valid values is written as ``n/a (no data)``, never as 0.
- Identifiers (flight_date, flight_id) and time ranges are never put in the prompt, to avoid leakage.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

SIGNALS = (
    "voltage_v", "current_a", "scale", "remaining",
    "temperature", "max_cell_voltage_delta", "discharged_mah",
)


def summarize_signal(values: Sequence[float | None]) -> dict:
    """Return n_total, n_missing and min/max/mean/std over non-missing, finite values (std is population std)."""
    valid = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    out = {"n_total": len(values), "n_missing": len(values) - len(valid)}
    if not valid:
        out.update(min=None, max=None, mean=None, std=None)
        return out
    mean = sum(valid) / len(valid)
    var = sum((v - mean) ** 2 for v in valid) / len(valid)
    out.update(min=min(valid), max=max(valid), mean=mean, std=math.sqrt(var))
    return out


def summarize_flight(rows: Mapping[str, Sequence[float | None]]) -> dict[str, dict]:
    missing = [s for s in SIGNALS if s not in rows]
    if missing:
        raise KeyError(f"missing signals: {missing}")
    return {s: summarize_signal(rows[s]) for s in SIGNALS}


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.4g}"


def build_prompt(summary: Mapping[str, dict], labels: Sequence[str]) -> str:
    """Build the classification prompt from a flight summary. Contains no identifiers."""
    lines = []
    for s in SIGNALS:
        d = summary[s]
        if d["min"] is None:
            lines.append(f"- {s}: n/a (no data)")
        else:
            gap = f", {d['n_missing']} of {d['n_total']} values missing" if d["n_missing"] else ""
            lines.append(f"- {s}: min={_fmt(d['min'])}, max={_fmt(d['max'])}, "
                         f"mean={_fmt(d['mean'])}, std={_fmt(d['std'])}{gap}")
    label_list = ", ".join(labels)
    return (
        "You are given summary statistics of one UAV flight (battery telemetry).\n"
        "Classify the flight into exactly one of these classes: " + label_list + ".\n"
        "Some signals may be unavailable (n/a). Do not assume a missing signal means a normal value.\n\n"
        "Statistics:\n" + "\n".join(lines) + "\n\n"
        'Answer with JSON only: {"class": "<one of the classes>"}'
    )
