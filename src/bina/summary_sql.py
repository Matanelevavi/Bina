"""Athena SQL that summarizes selected signals per flight (min/max/mean/std and non-null count).

Flights are addressed by (flight_date, time prefix), e.g. ("2019-03-19", "07_31_26"), and matched with
``starts_with(flight_id, '<prefix>_')`` because the topic/instance suffix of ``flight_id`` differs per table.
Columns are quoted, so names such as ``gyro_rad[0]`` work. Values must already be numeric in the table.
"""
from __future__ import annotations

import re
from typing import Sequence

Flight = tuple[str, str]

BATTERY_SIGNALS = ("voltage_v", "current_a", "scale", "remaining",
                   "temperature", "discharged_mah")
SENSOR_SIGNALS = ("gyro_rad[0]", "gyro_rad[1]", "gyro_rad[2]",
                  "accelerometer_m_s2[0]", "accelerometer_m_s2[1]", "accelerometer_m_s2[2]",
                  "baro_alt_meter", "baro_temp_celcius")

_PREFIX = re.compile(r"^\d{2}_\d{2}_\d{2}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}-{0,2}$")  # raw folders like "2021-10-06--" exist


# Short aliases used in the Athena queries that were actually run; the parser below relies on them.
ALIASES = {
    "discharged_mah": "mah",
    "gyro_rad[0]": "gx", "gyro_rad[1]": "gy", "gyro_rad[2]": "gz",
    "accelerometer_m_s2[0]": "ax", "accelerometer_m_s2[1]": "ay", "accelerometer_m_s2[2]": "az",
    "baro_alt_meter": "alt", "baro_temp_celcius": "btemp",
}


def _alias(col: str) -> str:
    return ALIASES.get(col) or re.sub(r"[^0-9a-zA-Z]+", "_", col).strip("_")


def _check(flights: Sequence[Flight]) -> None:
    if not flights:
        raise ValueError("no flights given")
    for d, p in flights:
        if not _DATE.match(d) or not _PREFIX.match(p):
            raise ValueError(f"bad flight reference: {(d, p)!r}")


def per_flight_summary_sql(table: str, signals: Sequence[str], flights: Sequence[Flight], instance: str = "0") -> str:
    """Per-flight summary SQL. Only files of the given instance (suffix ``_<instance>``) are used, so a flight
    with two instance files (``_0`` and ``_1``) cannot produce two rows."""
    _check(flights)
    parts = []
    for s in signals:
        a, q = _alias(s), f'"{s}"'
        parts.append(
            f"       COUNT({q}) AS {a}_n,\n"
            f"       MIN({q}) AS {a}_min,\n"
            f"       MAX({q}) AS {a}_max,\n"
            f"       AVG({q}) AS {a}_avg,\n"
            f"       STDDEV_POP({q}) AS {a}_std"
        )
    dates = ", ".join(f"'{d}'" for d in sorted({d for d, _ in flights}))
    cond = "\n      OR ".join(
        f"(flight_date = '{d}' AND starts_with(flight_id, '{p}_'))" for d, p in sorted(set(flights))
    )
    return (
        "SELECT flight_date,\n       flight_id,\n       COUNT(*) AS n_rows,\n"
        + ",\n".join(parts)
        + f"\nFROM bina_db.{table}\nWHERE flight_date IN ({dates})\n  AND (\n      {cond}\n  )\n"
        f"  AND regexp_like(flight_id, '_{instance}$')\n"
        "GROUP BY flight_date, flight_id\nORDER BY flight_date, flight_id;"
    )


def _num(x):
    if x is None or str(x).strip() == "":
        return None
    return float(x)


def summaries_from_row(row, signals: Sequence[str]) -> dict[str, dict]:
    """Turn one Athena result row (dict of strings, as in the CSV export) into per-signal summaries.

    A signal with zero non-null values gets None statistics. ``n_missing`` is n_rows minus the non-null count.
    """
    n_rows = int(row["n_rows"])
    out = {}
    for s in signals:
        a = _alias(s)
        n = int(row[f"{a}_n"])
        valid = n > 0
        out[s] = {
            "n_total": n_rows,
            "n_missing": n_rows - n,
            "min": _num(row[f"{a}_min"]) if valid else None,
            "max": _num(row[f"{a}_max"]) if valid else None,
            "mean": _num(row[f"{a}_avg"]) if valid else None,
            "std": _num(row[f"{a}_std"]) if valid else None,
        }
    return out
