"""Coherence dimension: do the reasoning steps logically follow from one
another, independent of whether the final answer is correct?"""

from utils.engine import evaluate_dimension
from utils.heuristics import heuristic_coherence
from utils.prompts import coherence_prompt

_PROMPT = coherence_prompt()


def evaluate_coherence(prompt: str, steps: list[str], answer: str) -> dict:
    return evaluate_dimension(_PROMPT, heuristic_coherence, prompt, steps, answer)
