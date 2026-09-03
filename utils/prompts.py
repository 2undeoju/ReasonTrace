"""LangChain prompt templates for every evaluation dimension.

Each template asks the model to focus on exactly one thing, and to
respond in a fixed two-line format (`Score: <int>` / `Feedback: <text>`)
so `utils.parsing.parse_score_feedback` can turn every response into
structured data the same way, regardless of which dimension asked.
"""

from langchain_core.prompts import ChatPromptTemplate

_RESPONSE_FORMAT = """
Return:
- A numeric score from 0 to 100 (integer).
- A short paragraph of constructive feedback.

Format your response EXACTLY as:
Score: <integer>
Feedback: <one paragraph>

Prompt:
{prompt}

Steps:
{steps}

Answer:
{answer}
"""


def coherence_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        """You are an expert university instructor evaluating a student's reasoning process.
You are given the assignment prompt, the student's step-by-step reasoning, and the final answer.

Your task:
1. Evaluate how logically coherent the reasoning steps are.
2. Check whether each step follows from the previous one.
3. Ignore whether the final answer is correct; focus on the reasoning quality.
"""
        + _RESPONSE_FORMAT
    )


def originality_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        """You are evaluating the originality of a student's reasoning process.
You are given the assignment prompt, the student's step-by-step reasoning, and the final answer.

Your task:
1. Judge whether the reasoning looks generic, boilerplate, or copy-pasted.
2. Reward specific, contextual, and personal reasoning.
3. Penalize vague, template-like, or suspiciously uniform reasoning.
"""
        + _RESPONSE_FORMAT
    )


def depth_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        """You are evaluating the conceptual depth of a student's reasoning.
You are given the assignment prompt, the student's step-by-step reasoning, and the final answer.

Your task:
1. Assess whether the student engages with concepts, not just surface-level statements.
2. Reward explanations, justifications, and connections between ideas.
3. Penalize shallow, purely procedural reasoning.
"""
        + _RESPONSE_FORMAT
    )


def integrity_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        """You are evaluating the integrity of a student's reasoning process.
You are given the assignment prompt, the student's step-by-step reasoning, and the final answer.

Your task:
1. Look for suspicious patterns (e.g. overly polished reasoning, inconsistent steps, signs of copy-paste).
2. You are NOT an AI detector -- do not claim to detect AI authorship. You can flag reasoning that
   looks implausible or inconsistent for a typical student, and nothing more than that.
3. Focus on internal consistency and plausibility, and say so explicitly in your feedback.

Return:
- A numeric score from 0 to 100 (integer), where higher means more internally consistent/plausible.
- A short paragraph of constructive feedback or a specific, evidence-based observation.

Format your response EXACTLY as:
Score: <integer>
Feedback: <one paragraph>

Prompt:
{prompt}

Steps:
{steps}

Answer:
{answer}
"""
    )
