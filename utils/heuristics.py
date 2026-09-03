"""Deterministic, no-API-key fallback scoring.

These are NOT a substitute for the LLM-based evaluation -- they're simple,
transparent proxies so the API is fully demoable (and free) with zero
setup, and so it degrades honestly instead of crashing when no
OPENAI_API_KEY is configured. Every response says clearly which mode
produced it (see `app.py`).

Each function below is intentionally simple and explainable in one
sentence, that's the point of a heuristic fallback: you should be able to
say exactly why it gave the score it did.
"""

from __future__ import annotations

import re

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "and", "in",
    "on", "for", "that", "this", "it", "as", "so", "then", "we", "you",
    "i", "be", "by", "with", "at", "from", "or", "which",
}

_JUSTIFICATION_MARKERS = (
    "because", "since", "therefore", "this means", "which shows",
    "in order to", "so that", "as a result", "this implies", "given that",
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def _content_words(text: str) -> set[str]:
    return {w for w in _words(text) if w not in _STOPWORDS and len(w) > 2}


def heuristic_coherence(steps: list[str]) -> dict:
    """Proxy for coherence: do consecutive steps share vocabulary, i.e. does
    each step plausibly pick up where the last one left off?"""
    if len(steps) < 2:
        return {
            "score": 50,
            "feedback": (
                "Only one reasoning step was provided, coherence between "
                "steps can't be assessed. (heuristic fallback)"
            ),
        }
    linked = 0
    for prev, curr in zip(steps, steps[1:]):
        if _content_words(prev) & _content_words(curr):
            linked += 1
    ratio = linked / (len(steps) - 1)
    score = round(ratio * 100)
    feedback = (
        f"{linked} of {len(steps) - 1} step transitions share vocabulary with "
        f"the step before them, a rough proxy for whether each step builds on "
        f"the last. (heuristic fallback, not an LLM judgment)"
    )
    return {"score": score, "feedback": feedback}


def heuristic_originality(steps: list[str]) -> dict:
    """Proxy for originality: lexical diversity and step length. Generic,
    boilerplate reasoning tends to be short and repetitive; specific
    reasoning tends to use a wider, less repetitive vocabulary."""
    all_words = _words(" ".join(steps))
    if not all_words:
        return {"score": 0, "feedback": "No text to evaluate. (heuristic fallback)"}
    diversity = len(set(all_words)) / len(all_words)
    avg_len = len(all_words) / max(len(steps), 1)
    # Blend diversity (0-1) and a length signal, capped, into a 0-100 score.
    length_signal = min(avg_len / 12, 1.0)  # 12+ words/step reads as "developed"
    score = round((0.6 * diversity + 0.4 * length_signal) * 100)
    feedback = (
        f"Vocabulary diversity is {diversity:.2f} (unique/total words) with an "
        f"average of {avg_len:.1f} words per step; low diversity and very short "
        f"steps usually indicate generic or templated reasoning. (heuristic fallback)"
    )
    return {"score": score, "feedback": feedback}


def heuristic_depth(steps: list[str]) -> dict:
    """Proxy for depth: presence of justification language (because, since,
    therefore, ...) relative to the number of steps."""
    text = " ".join(steps).lower()
    hits = sum(text.count(marker) for marker in _JUSTIFICATION_MARKERS)
    ratio = hits / max(len(steps), 1)
    score = round(min(ratio, 1.0) * 100)
    feedback = (
        f"Found {hits} justification cue(s) (e.g. 'because', 'therefore') across "
        f"{len(steps)} step(s); purely procedural steps with no justification "
        f"language score lower here. (heuristic fallback)"
    )
    return {"score": score, "feedback": feedback}


def heuristic_integrity(steps: list[str]) -> dict:
    """Proxy for integrity: flags suspiciously uniform step lengths, which
    can indicate templated or copy-pasted reasoning. This is explicitly NOT
    an AI-authorship detector, just a plausibility signal."""
    lengths = [len(s) for s in steps if s.strip()]
    if len(lengths) < 2:
        return {
            "score": 70,
            "feedback": "Too little text to assess plausibility. (heuristic fallback)",
        }
    mean_len = sum(lengths) / len(lengths)
    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    coefficient_of_variation = (variance ** 0.5) / mean_len if mean_len else 0
    # Real, human step-by-step reasoning is rarely perfectly uniform in length;
    # very low variation is treated as a mild plausibility flag, not a verdict.
    score = round(min(coefficient_of_variation * 200, 100))
    score = max(score, 30)  # never fully damn a submission on this signal alone
    feedback = (
        f"Step lengths have a coefficient of variation of {coefficient_of_variation:.2f}; "
        f"unusually uniform step lengths are a mild plausibility flag, not proof of anything. "
        f"(heuristic fallback, not an AI detector)"
    )
    return {"score": score, "feedback": feedback}
