"""Calling a Bedrock model through the Converse API and reading a JSON answer robustly.

The model was observed (Haiku 4.5, temperature 0) to wrap its answer in a ```json fence even when told
"JSON only", so parsing must not assume bare JSON. The boto3 client is injected, which keeps this testable.
"""
from __future__ import annotations

import json
import re
from typing import Any, Sequence

DEFAULT_MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> dict[str, Any]:
    """Return the first JSON object in ``text``, with or without a markdown fence."""
    m = _FENCE.search(text)
    candidate = m.group(1) if m else text
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in model output: {text[:80]!r}")
    return json.loads(candidate[start:end + 1])


def classify(client, prompt: str, labels: Sequence[str], model_id: str = DEFAULT_MODEL_ID,
             max_tokens: int = 200) -> dict[str, Any]:
    """Send one prompt and return {'class', 'explanation', 'raw', 'input_tokens', 'output_tokens', 'latency_ms'}.

    Raises ValueError if the answer is not parseable or names a class outside ``labels``;
    the caller decides whether to record the failure and continue.
    """
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    raw = resp["output"]["message"]["content"][0]["text"]
    obj = extract_json(raw)
    cls = obj.get("class")
    if cls not in labels:
        raise ValueError(f"class {cls!r} not in labels; raw={raw[:80]!r}")
    return {
        "class": cls,
        "explanation": obj.get("explanation"),
        "raw": raw,
        "input_tokens": resp["usage"]["inputTokens"],
        "output_tokens": resp["usage"]["outputTokens"],
        "latency_ms": resp["metrics"]["latencyMs"],
    }
