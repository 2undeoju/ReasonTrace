"""Originality dimension: does the reasoning look specific and genuine,
or generic and boilerplate?"""

from utils.engine import evaluate_dimension
from utils.heuristics import heuristic_originality
from utils.prompts import originality_prompt

_PROMPT = originality_prompt()


def evaluate_originality(prompt: str, steps: list[str], answer: str) -> dict:
    return evaluate_dimension(_PROMPT, heuristic_originality, prompt, steps, answer)
