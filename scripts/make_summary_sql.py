#!/usr/bin/env python3
"""Print the per-flight summary SQL for every flight in a flights JSON file.

Usage: python scripts/make_summary_sql.py data/sample.json battery|sensor > query.sql
"""
import json
import sys

from bina.summary_sql import BATTERY_SIGNALS, SENSOR_SIGNALS, per_flight_summary_sql

KINDS = {
    "battery": ("battery_status", BATTERY_SIGNALS),
    "sensor": ("sensor_combined", SENSOR_SIGNALS),
}


def main(flights_path: str, kind: str) -> None:
    table, signals = KINDS[kind]
    flights = [(f["flight_date"], f["flight"]) for f in json.load(open(flights_path))]
    print(per_flight_summary_sql(table, signals, flights))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in KINDS:
        sys.exit(__doc__)
    main(*sys.argv[1:])
