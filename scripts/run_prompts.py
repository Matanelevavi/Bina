#!/usr/bin/env python3
"""Run prompts from a JSON file on Bedrock (Converse API, temperature 0) and save the answers.

Self-contained on purpose (only boto3 and the standard library) so it can run in CloudShell without the repo.
Usage: python3 run_prompts.py prompts.json results.json
A failure on one prompt is recorded and the run continues.
"""
import json
import re
import sys

import boto3

MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
LABELS = ["Normal", "Altitude", "External Position", "Global Position", "Mechanical"]


def extract_class(text):
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    body = m.group(1) if m else text
    obj = json.loads(body[body.find("{"): body.rfind("}") + 1])
    if obj.get("class") not in LABELS:
        raise ValueError(f"unknown class: {obj.get('class')!r}")
    return obj["class"]


def main(prompts_path, out_path):
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    results = []
    for item in json.load(open(prompts_path)):
        rec = {"key": item["key"], "version": item["version"], "truth": item["truth"]}
        try:
            r = client.converse(
                modelId=MODEL_ID,
                messages=[{"role": "user", "content": [{"text": item["prompt"]}]}],
                inferenceConfig={"maxTokens": 100, "temperature": 0},
            )
            raw = r["output"]["message"]["content"][0]["text"]
            rec.update(raw=raw, input_tokens=r["usage"]["inputTokens"],
                       output_tokens=r["usage"]["outputTokens"], latency_ms=r["metrics"]["latencyMs"])
            rec["predicted"] = extract_class(raw)
        except Exception as e:  # record and continue
            rec["error"] = f"{type(e).__name__}: {e}"
        results.append(rec)
        print(rec["key"], rec["version"], "truth:", rec["truth"], "pred:", rec.get("predicted"),
              "tokens:", rec.get("input_tokens"), "/", rec.get("output_tokens"), rec.get("error", ""))
    json.dump(results, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
