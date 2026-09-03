"""Shared response parsing for every evaluation dimension.

Every LangChain prompt (coherence, originality, depth, integrity) is asked
to reply in the same two-line format:

    Score: <integer>
    Feedback: <one paragraph>

This is the single place that turns that text back into structured data,
so every dimension parses responses identically and a format fix only has
to happen in one place.
"""

from __future__ import annotations

import re

_SCORE_RE = re.compile(r"score\s*:\s*(-?\d+)", re.IGNORECASE)
_FEEDBACK_RE = re.compile(r"feedback\s*:\s*(.+)", re.IGNORECASE | re.DOTALL)


def parse_score_feedback(text: str) -> dict:
    """Parse a 'Score: N / Feedback: ...' formatted LLM response.

    Falls back gracefully (score 0, explanatory feedback) if the model
    didn't follow the format, instead of raising and taking the whole
    request down.
    """
    score_match = _SCORE_RE.search(text)
    feedback_match = _FEEDBACK_RE.search(text)

    score = int(score_match.group(1)) if score_match else 0
    score = max(0, min(100, score))  # clamp into a sane 0-100 range

    if feedback_match:
        feedback = feedback_match.group(1).strip().splitlines()[0].strip()
    else:
        feedback = text.strip()[:300] or "No feedback provided."

    return {"score": score, "feedback": feedback}
