"""Pick a few calibration flights that are NOT part of the evaluation sample.

Prompt tuning on flights that are later scored would bias the evaluation, so calibration
flights come from the pool minus the sample. By default flights that share a flight_date
with any sample flight are also avoided (same-day flights are often near-duplicates);
if a requested stratum would then be empty, the date rule is relaxed for that stratum and
the relaxation is reported back, never applied silently.
"""
from __future__ import annotations

import random
from typing import Any, Mapping, Sequence

Stratum = tuple[str, bool]  # (class, has_gps)


def pick_calibration(
    pool: Sequence[Mapping[str, Any]],
    sample: Sequence[Mapping[str, Any]],
    strata: Sequence[Stratum],
    seed: int = 7,
) -> list[dict[str, Any]]:
    """Return one flight per stratum, each with a ``same_date_as_sample`` flag."""
    sample_keys = {f["key"] for f in sample}
    sample_dates = {f["flight_date"] for f in sample}
    rng = random.Random(seed)
    chosen: list[dict[str, Any]] = []
    for cls, gps in strata:
        cands = sorted(
            (f for f in pool if f["class"] == cls and bool(f["has_gps"]) == gps and f["key"] not in sample_keys),
            key=lambda f: f["key"],
        )
        if not cands:
            raise ValueError(f"no candidate flights for {(cls, gps)}")
        clean = [f for f in cands if f["flight_date"] not in sample_dates]
        use = clean or cands
        pick = dict(rng.choice(use))
        pick["same_date_as_sample"] = not clean
        chosen.append(pick)
    return chosen
