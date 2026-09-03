# ReasonTrace

A LangChain-powered API that evaluates **how students think**, not just
**what answer they give**.

Instead of grading only the final output, ReasonTrace analyses a
student's step-by-step reasoning trace and scores it across four
dimensions:

- **Coherence** — do the steps logically follow from one another?
- **Originality** — does the reasoning look specific and genuine, or generic and boilerplate?
- **Depth** — does the student engage with concepts, or just skim the surface?
- **Integrity** — is the reasoning internally consistent and plausible? (explicitly *not* an AI-authorship detector, see below)

This is a companion project to
[`reasoning-step-grader`](https://github.com/2undeoju/reasoning-step-grader),
which verifies the *arithmetic* correctness of a step-by-step solution.
ReasonTrace asks a different question: even when a step is arithmetically
fine, is the reasoning itself any good?

## Does this need an OpenAI key?

**No, not to try it.** ReasonTrace runs in one of two modes, and it picks
automatically based on whether `OPENAI_API_KEY` is set:

- **Heuristic mode (default, zero setup)** — each dimension is scored by a
  small, transparent, deterministic proxy (vocabulary overlap between
  steps, lexical diversity, presence of justification language like
  "because"/"therefore", uniformity of step length). Every response says
  `"mode": "heuristic"` and each dimension's feedback ends with
  `(heuristic fallback)`, so it's never presented as more than it is.
- **LLM mode** — set `OPENAI_API_KEY` (in your shell, or in a `.env` file,
  see `.env.example`) and every dimension is instead scored by a
  `gpt-4o-mini` call through a real LangChain prompt template. Responses
  switch to `"mode": "llm"` automatically, no code changes needed.

Run `python demo.py` right now, with nothing configured, and you'll see
heuristic-mode scores on three contrasting example traces. Set the key
and run it again to see LLM-mode scores instead.

## What actually works right now

- The FastAPI app starts, and both `/` and `/health` respond.
- `POST /evaluate` runs all four dimensions **concurrently** (via
  `asyncio.gather`), returns an aggregate `overall_score`, and raises
  `flags` when coherence or integrity comes back low.
- Heuristic mode has been run end-to-end (see `demo.py` output below) and
  correctly separates a strong, justified reasoning trace from a weak,
  generic one and from a suspicious, templated-looking one, without
  calling any external API.
- Input validation rejects empty prompts, empty step lists, or all-blank
  steps with a clear 422, instead of crashing downstream.
- If an LLM call fails for any reason (bad key, rate limit, network),
  that dimension falls back to its heuristic instead of taking the whole
  request down, and says so in its feedback.

## What's still a prototype, not production

- The heuristics are intentionally simple linguistic proxies, not a
  validated grading rubric. They're there so the API is demoable for
  free, not as a claim that they grade as well as an instructor (or the
  LLM path) would.
- The **integrity** dimension is a plausibility signal only. It is
  explicitly not, and does not claim to be, an AI-authorship detector,
  the prompt and the heuristic both say so on purpose, because that's an
  honest line to hold given how unreliable AI detectors actually are.
- There's no persistence layer yet (no database, no per-student history)
  and no auth on the API. Fine for a portfolio demo, not fine to point at
  real student data as-is.
- LLM-mode has been code-reviewed and structured correctly (LCEL
  `prompt | llm` chains, proper error handling) but not run against a
  live OpenAI account in this pass, since that requires a paid key. If
  you add one, `demo.py` will exercise it end to end.

## Architecture

```text
reasontrace/
├── app.py                        # FastAPI app: /, /health, /evaluate
├── demo.py                       # zero-setup CLI demo, no server needed
├── chains/
│   ├── coherence.py              # thin wrapper: prompt + heuristic -> evaluate_dimension
│   ├── originality.py
│   ├── depth.py
│   └── integrity.py
├── utils/
│   ├── engine.py                 # shared LLM-or-heuristic evaluation logic
│   ├── prompts.py                # LangChain prompt templates, one per dimension
│   ├── parsing.py                # shared "Score: N / Feedback: ..." parser
│   └── heuristics.py             # deterministic no-API-key fallback scoring
├── examples/
│   ├── sample_trace_strong.json      # detailed, justified reasoning
│   ├── sample_trace_weak.json        # generic, unjustified reasoning
│   └── sample_trace_suspicious.json  # uniform, templated-looking steps
├── requirements.txt
├── .env.example
└── README.md
```

The four `chains/*.py` files stay separate on purpose, one file per
evaluation dimension, but share one engine (`utils/engine.py`) and one
parser (`utils/parsing.py`), so there's no duplicated LLM plumbing across
them. Adding a fifth dimension means adding a prompt, a heuristic, and a
five-line wrapper file, not touching the other four.

## Install and run

```bash
git clone https://github.com/<your-username>/reasontrace.git
cd reasontrace

python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Optional: enables LLM-mode scoring instead of heuristic mode.
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

**Fastest way to see it work, no server needed:**

```bash
python demo.py
```

**Or run it as a real API:**

```bash
uvicorn app:app --reload
# then open http://127.0.0.1:8000/docs for interactive Swagger UI
```

```bash
curl -X POST "http://127.0.0.1:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d @examples/sample_trace_strong.json
```

### Sample output (heuristic mode, no key needed)

Running `python demo.py` against the weak trace
(`"Use the formula." / "Do the division." / "Get the answer."`) produces:

```json
{
  "mode": "heuristic",
  "overall_score": 22,
  "flags": [
    "Low integrity score: reasoning trace looks unusually uniform or implausible.",
    "Low coherence score: steps don't clearly build on one another."
  ],
  "coherence":   {"score": 0,  "feedback": "0 of 2 step transitions share vocabulary with the step before them... (heuristic fallback, not an LLM judgment)"},
  "originality": {"score": 57, "feedback": "Vocabulary diversity is 0.78... (heuristic fallback)"},
  "depth":       {"score": 0,  "feedback": "Found 0 justification cue(s)... (heuristic fallback)"},
  "integrity":   {"score": 30, "feedback": "Step lengths have a coefficient of variation of 0.03... (heuristic fallback, not an AI detector)"}
}
```

Against the detailed, justified trace in `sample_trace_strong.json`, the
same run scores 71/100 overall with no flags, the tool visibly tells the
two apart without ever calling an external API.

## Why this, and why now

Universities are facing three real, current pressures this maps onto:

1. **Grading at scale.** Detailed, step-level feedback is the most
   valuable kind for learning and the least scalable for an instructor to
   give by hand, especially in a project-based model, where the focus is
   on *how* someone reasoned, not just their final result.
2. **Academic integrity is shifting.** AI has made a polished final
   answer trivial to produce. Institutions are moving from AI-detection
   tools toward assessments built around process and reasoning traces
   instead (Inside Higher Ed, ["AI Detectors Are Out, New Assessments Are
   In,"](https://www.insidehighered.com/news/tech-innovation/artificial-intelligence/2026/08/05/ai-detectors-are-out-new-approaches-are)
   Aug 2026). A tool that scores the trace, not just the output, is built
   for that shift.
3. **Faculty confidence in student thinking is eroding.** Recent College
   Board research found near-universal faculty concern that AI is
   undermining students' original writing and critical thinking. A tool
   that requires and rewards a visible, justified reasoning process pushes
   incentives back toward genuine thinking.

## Extending the project

- **Web dashboard** — visualize scores over time for a class or cohort.
- **Rubric integration** — let instructors define custom weightings per dimension.
- **Course-specific prompts** — tune the four prompt templates per discipline (math vs. philosophy vs. code).
- **Oral defense support** — pair a low-confidence trace with suggested follow-up questions for a viva-style check-in.
- **LMS export** — push results into Moodle/Canvas via their APIs.

## Stack

Python, FastAPI, Pydantic v2, LangChain (`langchain-core` for prompt
templates, `langchain` + `langchain-openai` for the LLM path), python-dotenv.
