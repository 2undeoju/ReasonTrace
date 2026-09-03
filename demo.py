"""Zero-setup demo: exercises the /evaluate endpoint in-process (no need to
run `uvicorn` or make a real HTTP call) against three contrasting example
traces, so you can see the four dimensions actually discriminate between a
strong, a weak, and a suspicious-looking submission.

Run it:
    python demo.py

Works with no API key (heuristic fallback mode). Set OPENAI_API_KEY first
if you want to see LLM-scored feedback instead.
"""

import json
import os

from fastapi.testclient import TestClient

from app import app

EXAMPLES = [
    ("STRONG (detailed, justified reasoning)", "examples/sample_trace_strong.json"),
    ("WEAK (generic, no justification)", "examples/sample_trace_weak.json"),
    ("SUSPICIOUS (uniform, templated-looking steps)", "examples/sample_trace_suspicious.json"),
]


def main() -> None:
    client = TestClient(app)
    mode = "LLM mode (OPENAI_API_KEY detected)" if os.environ.get("OPENAI_API_KEY") else "heuristic mode (no API key needed)"
    print(f"ReasonTrace demo -- running in {mode}\n")
    print("=" * 78)

    for label, path in EXAMPLES:
        with open(path) as f:
            payload = json.load(f)

        response = client.post("/evaluate", json=payload)
        response.raise_for_status()
        result = response.json()

        print(f"\n{label}")
        print(f"  Prompt: {payload['prompt']}")
        print(f"  Steps ({len(payload['steps'])}):")
        for i, step in enumerate(payload["steps"], start=1):
            print(f"    {i}. {step}")
        print(f"  Overall score: {result['overall_score']}/100  (mode: {result['mode']})")
        for dim in ("coherence", "originality", "depth", "integrity"):
            d = result[dim]
            print(f"    - {dim.capitalize():<12} {d['score']:>3}/100  {d['feedback']}")
        if result["flags"]:
            print("  Flags:")
            for flag in result["flags"]:
                print(f"    ! {flag}")
        print("-" * 78)

    print("\nDone. Try `uvicorn app:app --reload` and open /docs to call it live.")


if __name__ == "__main__":
    main()
