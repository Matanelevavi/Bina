"""Classification metrics for the anomaly-type evaluation (no external dependencies)."""
from __future__ import annotations

from collections import Counter
from typing import Sequence


def confusion_matrix(y_true: Sequence[str], y_pred: Sequence[str]) -> Counter:
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    return Counter(zip(y_true, y_pred))


def precision_recall(y_true: Sequence[str], y_pred: Sequence[str]) -> dict[str, dict[str, float | int]]:
    """Per-class precision, recall, f1 and support. Undefined ratios are reported as 0.0."""
    cm = confusion_matrix(y_true, y_pred)
    labels = sorted(set(y_true) | set(y_pred))
    result: dict[str, dict[str, float | int]] = {}
    for c in labels:
        tp = cm[(c, c)]
        fp = sum(v for (t, p), v in cm.items() if p == c and t != c)
        fn = sum(v for (t, p), v in cm.items() if t == c and p != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        result[c] = {"precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
    return result


def accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if not y_true:
        raise ValueError("empty input")
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)
