"""The shared evaluation engine every dimension (coherence, originality,
depth, integrity) calls into.

This is the one place that decides HOW a dimension gets evaluated:

- If OPENAI_API_KEY is set, build an LCEL chain (`prompt | llm`) with the
  dimension's own prompt template, invoke it, and parse the response.
- If not, fall back to that dimension's deterministic heuristic, so the
  API stays fully functional (and free) with zero setup.

Individual files under chains/ stay thin: each just supplies its own
prompt template and heuristic function to `evaluate_dimension`, they don't
duplicate the LLM plumbing or the parsing logic.
"""

from __future__ import annotations

import os
from typing import Callable

from langchain_core.prompts import ChatPromptTemplate

from utils.parsing import parse_score_feedback

_llm = None  # lazily constructed, only if/when we actually have a key


def _get_llm():
    global _llm
    if _llm is None:
        from langchain_openai import ChatOpenAI

        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return _llm


def llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def evaluate_dimension(
    prompt_template: ChatPromptTemplate,
    heuristic_fn: Callable[[list[str]], dict],
    prompt: str,
    steps: list[str],
    answer: str,
) -> dict:
    """Evaluate one dimension, using the LLM if available, otherwise the
    dimension's heuristic fallback. Always returns
    {"score": int, "feedback": str, "mode": "llm" | "heuristic"}.
    """
    formatted_steps = "\n".join(f"- {s}" for s in steps)

    if llm_available():
        try:
            chain = prompt_template | _get_llm()
            response = chain.invoke({"prompt": prompt, "steps": formatted_steps, "answer": answer})
            result = parse_score_feedback(response.content)
            result["mode"] = "llm"
            return result
        except Exception as exc:  # noqa: BLE001 - never let one dimension take the API down
            fallback = heuristic_fn(steps)
            fallback["mode"] = "heuristic"
            fallback["feedback"] += f" (LLM call failed, used fallback: {exc})"
            return fallback

    result = heuristic_fn(steps)
    result["mode"] = "heuristic"
    return result
