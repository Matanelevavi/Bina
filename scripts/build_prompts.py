#!/usr/bin/env python3
"""Build classification prompts (version A: battery only, version B: battery + motion sensors) from Athena CSV exports.

Usage: python scripts/build_prompts.py battery.csv sensor.csv out.json
Each CSV is the result of the per-flight summary queries (one row per flight). Rows are matched by
(flight_date, time prefix of flight_id). The output holds one record per flight and version, with the
ground-truth class kept OUT of the prompt text.
"""
import csv
import json
import sys

from bina.features import build_prompt, mark_not_reported
from bina.summary_sql import BATTERY_SIGNALS, summaries_from_row

LABELS = ["Normal", "Altitude", "External Position", "Global Position", "Mechanical"]
SENSOR_B = ("gyro_rad[0]", "gyro_rad[1]", "gyro_rad[2]",
            "accelerometer_m_s2[0]", "accelerometer_m_s2[1]", "accelerometer_m_s2[2]", "baro_alt_meter")


def _index(path):
    idx = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            k = (r["flight_date"], r["flight_id"][:8])
            if k in idx:
                raise ValueError(f"duplicate rows for flight {k} in {path}")
            idx[k] = r
    return idx


def main(battery_csv, sensor_csv, out_path, flights_path="data/calibration.json"):
    # flights_path may also be data/sample.json (same record format)
    bat, sen = _index(battery_csv), _index(sensor_csv)
    out = []
    for f in json.load(open(flights_path)):
        k = (f["flight_date"], f["flight"])
        a = summaries_from_row(bat[k], BATTERY_SIGNALS)
        b = {**a, **summaries_from_row(sen[k], SENSOR_B)}
        for version, summ, source in (("A", a, "battery telemetry"), ("B", b, "battery and motion-sensor telemetry")):
            out.append({"key": f["key"], "truth": f["class"], "version": version,
                        "prompt": build_prompt(mark_not_reported(summ), LABELS, source)})
    json.dump(out, open(out_path, "w"), indent=1, ensure_ascii=False)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
