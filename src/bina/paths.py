"""Parsing of raw-bucket object keys.

The Glue jobs read raw CSVs with a glob that matches exactly one folder level
between the raw prefix and the file (``<flight_date>/<file>.csv``). Files that
live deeper (``<date>/sessNNN/logNNN/<file>.csv``) are silently skipped, so the
helpers here make that rule explicit and testable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FILE = re.compile(r"^(?P<flight>.+?)_(?P<topic>battery_status|actuator_outputs|sensor_combined)_\d+\.csv$")


@dataclass(frozen=True)
class RawKey:
    flight_date: str | None
    depth: int
    filename: str

    @property
    def matched_by_glob(self) -> bool:
        """True if the Glue glob ``*/*<topic>*.csv`` (depth 2) would match this key."""
        return self.depth == 2 and self.flight_date is not None


def parse_raw_key(key: str) -> RawKey:
    """Parse a key relative to the raw prefix, e.g. ``2019-01-04/08_01_09_battery_status_0.csv``."""
    parts = [p for p in key.strip("/").split("/") if p]
    if not parts:
        raise ValueError("empty key")
    date = parts[0] if _DATE.match(parts[0]) else None
    return RawKey(flight_date=date, depth=len(parts), filename=parts[-1])


def flight_id_from_filename(filename: str) -> str:
    """Mirror of the Glue ``regexp_extract(source_file, '^(.*)\\.csv$')`` step on the file name."""
    m = re.match(r"^(.*)\.csv$", filename)
    if not m:
        raise ValueError(f"not a csv file: {filename!r}")
    return m.group(1)
