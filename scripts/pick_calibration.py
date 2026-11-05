#!/usr/bin/env python3
"""Usage: python scripts/pick_calibration.py pool.json sample.json"""
import json
import sys

from bina.calibration import pick_calibration

STRATA = [("Normal", False), ("Altitude", False), ("Global Position", True)]


def main(pool_path: str, sample_path: str) -> None:
    pool = json.load(open(pool_path))
    sample = json.load(open(sample_path))
    for f in pick_calibration(pool, sample, STRATA):
        print(json.dumps(f))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
