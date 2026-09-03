# ReasonTrace

**Grades the thinking, not just the answer.**

ReasonTrace looks at *how* a student worked through a problem, step by
step, and scores the reasoning itself. Not just whether the final number
was right.

---

## What is this, in plain terms

Most grading, human or automated, looks at one thing: was the final
answer correct. That misses something important: two students can land
on the same right answer, one through solid, well-justified thinking, the
other through a lucky guess or a copied line. A grader that only checks
the final answer can't tell those apart. ReasonTrace can.

You give it a problem, a student's step-by-step reasoning, and their
final answer. It hands back a score, out of 100, across four things that
actually matter for learning:

| Dimension | What it's really asking |
|---|---|
| **Coherence** | Does each step actually follow from the one before it? |
| **Originality** | Does this look like genuine thinking, or a generic template? |
| **Depth** | Is the student engaging with *why*, or just going through the motions? |
| **Integrity** | Does the whole trace hang together and look plausible? |

It's built to run two ways: for free, with nothing to set up, using
built-in scoring rules, or, if you give it an OpenAI key, using a real
language model for richer, more nuanced feedback. Either way, it always
tells you which one produced the score, nothing is dressed up as more
than it is.

## Why this, why now

Three pressures every university is feeling right now, that this speaks
directly to:

1. **Instructors can't hand-grade reasoning at scale.** Step-by-step
   feedback is the most useful kind for learning and the least scalable
   to give by hand, especially in project-based courses where *how*
   someone thinks matters more than the final number.
2. **A polished final answer no longer proves anything.** AI has made
   that trivial to produce. Institutions are already shifting assessment
   away from checking answers and toward checking process
   ([Inside Higher Ed, Aug 2026](https://www.insidehighered.com/news/tech-innovation/artificial-intelligence/2026/08/05/ai-detectors-are-out-new-approaches-are)).
   ReasonTrace grades the process.
3. **Faculty trust in student thinking is eroding.** Recent College Board
   research found near-universal faculty concern that AI is undermining
   original thinking. Rewarding visible, justified reasoning is a more
   constructive answer to that than trying to detect and ban AI use.

## See it work

Run one command, no setup, no API key:

```bash
python demo.py
```

It scores three example submissions to the same problem, and the
difference is immediate:

| Submission | What it looks like | Overall score |
|---|---|---|
| **Weak** | `"Use the formula." "Do the division." "Get the answer."` | **22 / 100** |
| **Suspicious** | Five oddly uniform, templated-looking steps | **48 / 100**, flagged |
| **Strong** | Fully worked, each step justified in its own words | **71 / 100**, no flags |

Same problem, same final answer in every case, three very different
scores, because the reasoning itself is what's being judged.

---

## For the technical reader

### Does it need an OpenAI key?

**No.** ReasonTrace runs in one of two modes and picks automatically:

- **Heuristic mode (default)** — each dimension is scored by a small,
  transparent rule (vocabulary overlap between steps, lexical diversity,
  presence of justification language like "because"/"therefore",
  uniformity of step length). Zero cost, zero setup, and every response
  is labelled `"mode": "heuristic"` so it's never overstated.
- **LLM mode** — set `OPENAI_API_KEY` and every dimension is instead
  scored by `gpt-4o-mini` through a real LangChain prompt. Responses
  switch to `"mode": "llm"` automatically, no code changes needed. If a
  call ever fails, that one dimension quietly falls back to its
  heuristic instead of taking the whole request down.

### Stack

Python · FastAPI · Pydantic v2 · LangChain (`langchain-core` for prompt
templates, `langchain` + `langchain-openai` for the LLM path) ·
python-dotenv

### Install and run

```bash
git clone https://github.com/2undeoju/reasontrace.git
cd reasontrace

python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional, enables LLM mode instead of heuristic mode:
cp .env.example .env          # then add OPENAI_API_KEY=sk-... inside
```

```bash
python demo.py                       # fastest: no server needed
# or
uvicorn app:app --reload             # real API, docs at /docs
curl -X POST "http://127.0.0.1:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d @examples/sample_trace_strong.json
```

### How it's organized

```text
reasontrace/
├── app.py                 # FastAPI app: /, /health, /evaluate
├── demo.py                # zero-setup CLI demo, no server needed
├── chains/                # one thin file per dimension (coherence, originality, depth, integrity)
├── utils/
│   ├── engine.py          # shared LLM-or-heuristic evaluation logic
│   ├── prompts.py         # one LangChain prompt template per dimension
│   ├── parsing.py         # shared response parser
│   └── heuristics.py      # the no-API-key fallback scoring
├── examples/               # strong / weak / suspicious sample traces
├── requirements.txt
└── .env.example
```

Each `chains/*.py` file is five lines: it supplies a prompt and a
heuristic, and calls the shared engine. Adding a fifth dimension means
adding a prompt, a heuristic, and a five-line file, not touching the
other four.

### What actually works today

- FastAPI app boots; `/`, `/health`, and `/evaluate` all respond.
- `/evaluate` runs all four dimensions **concurrently**, returns an
  `overall_score`, and raises `flags` when coherence or integrity is low.
- Heuristic mode has been run end-to-end and reliably separates strong,
  weak, and suspicious traces, verified live, not just in theory.
- Bad input (empty prompt, empty steps) is rejected with a clear error
  instead of crashing downstream.

### What's still a prototype

- The heuristics are simple, explainable proxies, not a validated grading
  rubric. They exist so the tool is free to try, not as a claim they
  grade as well as an instructor or the LLM path would.
- **Integrity is a plausibility signal, not an AI-detector.** It doesn't
  claim to identify AI-written work, on purpose, because AI detectors are
  notoriously unreliable and claiming otherwise would be dishonest.
- No database, no per-student history, no auth yet. Fine for a demo, not
  yet for real student data.
- LLM mode is fully built and code-reviewed but hasn't been run against a
  live paid OpenAI account in this pass, add a key and `demo.py` will
  exercise it end to end.

### What's next

- A dashboard to visualize scores across a class or cohort
- Instructor-defined rubric weightings per dimension
- Discipline-specific prompt tuning (math vs. philosophy vs. code)
- LMS export (Moodle, Canvas)

---

**Companion project:** [`reasoning-step-grader`](https://github.com/2undeoju/reasoning-step-grader)
checks the *arithmetic* correctness of a step-by-step solution.
ReasonTrace asks the next question: even when the arithmetic is right, is
the reasoning itself any good?
