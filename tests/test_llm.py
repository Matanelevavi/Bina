import pytest
from bina.llm import extract_json, classify

LABELS = ["Normal", "Altitude"]


@pytest.mark.parametrize("text", [
    '```json\n{"class": "Normal"}\n```',
    '{"class": "Normal"}',
    'Sure! Here you go: {"class": "Normal"} hope it helps',
    '```\n{"class": "Normal"}\n```',
])
def test_extract_json_variants(text):
    assert extract_json(text) == {"class": "Normal"}


def test_no_json_raises():
    with pytest.raises(ValueError):
        extract_json("I cannot decide")


class FakeClient:
    def __init__(self, text):
        self.text, self.kwargs = text, None

    def converse(self, **kwargs):
        self.kwargs = kwargs
        return {"output": {"message": {"content": [{"text": self.text}]}},
                "usage": {"inputTokens": 85, "outputTokens": 14}, "metrics": {"latencyMs": 704}}


def test_classify_ok_and_temperature_zero():
    c = FakeClient('```json\n{"class": "Altitude"}\n```')
    r = classify(c, "p", LABELS)
    assert r["class"] == "Altitude" and r["input_tokens"] == 85 and r["latency_ms"] == 704
    assert c.kwargs["inferenceConfig"]["temperature"] == 0


def test_unknown_label_rejected():
    with pytest.raises(ValueError):
        classify(FakeClient('{"class": "Banana"}'), "p", LABELS)


def test_truncated_output_rejected():
    with pytest.raises(ValueError):
        classify(FakeClient('```json\n{"class": "Nor'), "p", LABELS)


def test_explanation_returned():
    c = FakeClient('```json\n{"class": "Normal", "explanation": "stable voltage"}\n```')
    assert classify(c, "p", LABELS)["explanation"] == "stable voltage"
    assert c.kwargs["inferenceConfig"]["maxTokens"] == 200
