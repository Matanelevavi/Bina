"""Generate Athena SQL that targets an exact list of flights.

Filtering on ``flight_date`` (the partition column) first lets Athena prune
partitions; the ``(flight_date, flight_id)`` pairs then pick exact flights.
"""
from __future__ import annotations

from typing import Iterable, Sequence

Pair = tuple[str, str]


def _q(value: str) -> str:
    if "'" in value:
        raise ValueError(f"unexpected quote in {value!r}")
    return "'%s'" % value


def where_clause(pairs: Iterable[Pair]) -> str:
    pairs = sorted(set(pairs))
    if not pairs:
        raise ValueError("no flights given")
    dates = sorted({d for d, _ in pairs})
    in_list = ", ".join(_q(d) for d in dates)
    cond = "\n      OR ".join(f"(flight_date = {_q(d)} AND flight_id = {_q(f)})" for d, f in pairs)
    return f"WHERE flight_date IN ({in_list})\n  AND (\n      {cond}\n  )"


def count_and_avg(table: str, column: str, pairs: Sequence[Pair]) -> tuple[str, str]:
    """Return (count_sql, avg_sql) for a list of flights."""
    w = where_clause(pairs)
    count_sql = f"SELECT COUNT(DISTINCT flight_id) AS flights\nFROM {table}\n{w};"
    avg_sql = f"SELECT AVG({column}) AS avg_{column}\nFROM {table}\n{w};"
    return count_sql, avg_sql
