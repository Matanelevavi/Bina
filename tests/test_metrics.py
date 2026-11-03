import pytest
from bina.metrics import precision_recall, accuracy, confusion_matrix


def test_known_values():
    t = ["a", "a", "a", "b", "b"]
    p = ["a", "a", "b", "b", "a"]
    r = precision_recall(t, p)
    assert r["a"]["precision"] == pytest.approx(2 / 3)
    assert r["a"]["recall"] == pytest.approx(2 / 3)
    assert r["b"]["support"] == 2
    assert accuracy(t, p) == pytest.approx(3 / 5)
    assert confusion_matrix(t, p)[("a", "b")] == 1


def test_undefined_is_zero():
    r = precision_recall(["a", "a"], ["a", "b"])
    assert r["b"]["precision"] == 0.0 and r["b"]["recall"] == 0.0


def test_length_mismatch():
    with pytest.raises(ValueError):
        precision_recall(["a"], [])
