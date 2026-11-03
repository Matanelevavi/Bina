"""Stratified sampling of flights for the evaluation set."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Iterable, Mapping


def stratified_sample(
    flights: Iterable[Mapping[str, Any]],
    quota: Mapping[tuple[str, bool], int],
    seed: int = 42,
) -> list[Mapping[str, Any]]:
    """Pick ``quota[(class, has_gps)]`` flights from every (class, has_gps) stratum.

    Raises if a stratum has fewer flights than requested, so a silently smaller
    sample can never be produced.
    """
    strata: dict[tuple[str, bool], list[Mapping[str, Any]]] = defaultdict(list)
    for f in flights:
        strata[(f["class"], bool(f["has_gps"]))].append(f)

    rng = random.Random(seed)
    out: list[Mapping[str, Any]] = []
    for stratum in sorted(quota):
        need = quota[stratum]
        pool = sorted(strata.get(stratum, []), key=lambda f: f["key"])
        if len(pool) < need:
            raise ValueError(f"stratum {stratum} has {len(pool)} flights, need {need}")
        out.extend(rng.sample(pool, need))
    return out


def summarize(sample: Iterable[Mapping[str, Any]]) -> dict[tuple[str, bool], int]:
    counts: dict[tuple[str, bool], int] = defaultdict(int)
    for f in sample:
        counts[(f["class"], bool(f["has_gps"]))] += 1
    return dict(counts)


def gps_leakage(sample: Iterable[Mapping[str, Any]]) -> dict[str, tuple[int, int]]:
    """Per class: (flights with GPS, total). A class that is always/never with GPS leaks its label."""
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for f in sample:
        stats[f["class"]][1] += 1
        stats[f["class"]][0] += bool(f["has_gps"])
    return {k: (v[0], v[1]) for k, v in stats.items()}
