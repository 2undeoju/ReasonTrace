"""Integrity dimension: is the reasoning internally consistent and
plausible? This is explicitly NOT an AI-authorship detector, only a
plausibility signal (see utils/prompts.py and utils/heuristics.py)."""

from utils.engine import evaluate_dimension
from utils.heuristics import heuristic_integrity
from utils.prompts import integrity_prompt

_PROMPT = integrity_prompt()


def evaluate_integrity(prompt: str, steps: list[str], answer: str) -> dict:
    return evaluate_dimension(_PROMPT, heuristic_integrity, prompt, steps, answer)
