"""Depth dimension: does the student engage with the underlying concepts,
or just execute steps procedurally?"""

from utils.engine import evaluate_dimension
from utils.heuristics import heuristic_depth
from utils.prompts import depth_prompt

_PROMPT = depth_prompt()


def evaluate_depth(prompt: str, steps: list[str], answer: str) -> dict:
    return evaluate_dimension(_PROMPT, heuristic_depth, prompt, steps, answer)
