"""ReasonTrace API -- evaluate student reasoning traces, not just final answers.

Run it:
    uvicorn app:app --reload

Then either:
    curl -X POST http://127.0.0.1:8000/evaluate -H "Content-Type: application/json" \\
        -d @examples/sample_trace_strong.json

or open http://127.0.0.1:8000/docs for interactive Swagger UI.

Works with zero setup: if OPENAI_API_KEY isn't set, every dimension falls
back to a deterministic heuristic (see utils/heuristics.py) instead of
failing, and the response tells you which mode produced each score.
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

load_dotenv()  # picks up OPENAI_API_KEY from a local .env if present

from chains.coherence import evaluate_coherence
from chains.depth import evaluate_depth
from chains.integrity import evaluate_integrity
from chains.originality import evaluate_originality
from utils.engine import llm_available

app = FastAPI(
    title="ReasonTrace API",
    description="Evaluate student reasoning traces, not just final answers.",
    version="0.2.0",
)


class EvaluationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The assignment/problem prompt.")
    steps: list[str] = Field(..., min_length=1, description="The student's reasoning steps, in order.")
    answer: str = Field(..., min_length=1, description="The student's final answer.")

    @field_validator("steps")
    @classmethod
    def steps_not_blank(cls, value: list[str]) -> list[str]:
        cleaned = [s.strip() for s in value if s.strip()]
        if not cleaned:
            raise ValueError("steps must contain at least one non-empty entry")
        return cleaned


@app.get("/")
async def root():
    return {
        "name": "ReasonTrace API",
        "status": "ok",
        "mode": "llm" if llm_available() else "heuristic (no OPENAI_API_KEY set)",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/evaluate")
async def evaluate_trace(payload: EvaluationRequest):
    # The four dimensions are independent, so run them concurrently rather
    # than one after another -- this matters most in LLM mode, where each
    # call is a network round trip.
    coherence, originality, depth, integrity = await asyncio.gather(
        asyncio.to_thread(evaluate_coherence, payload.prompt, payload.steps, payload.answer),
        asyncio.to_thread(evaluate_originality, payload.prompt, payload.steps, payload.answer),
        asyncio.to_thread(evaluate_depth, payload.prompt, payload.steps, payload.answer),
        asyncio.to_thread(evaluate_integrity, payload.prompt, payload.steps, payload.answer),
    )

    scores = [coherence["score"], originality["score"], depth["score"], integrity["score"]]
    overall = round(sum(scores) / len(scores))

    flags = []
    if integrity["score"] < 50:
        flags.append("Low integrity score: reasoning trace looks unusually uniform or implausible.")
    if coherence["score"] < 40:
        flags.append("Low coherence score: steps don't clearly build on one another.")

    return {
        "mode": "llm" if llm_available() else "heuristic",
        "overall_score": overall,
        "flags": flags,
        "coherence": coherence,
        "originality": originality,
        "depth": depth,
        "integrity": integrity,
    }
