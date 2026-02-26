# AGENTS.md --- QuizMaster (3-agent quiz show)

This repo hosts a 3-agent system (OpenClaw agents) that runs a
multiple-choice quiz game:

-   Researcher: gathers and/or generates quiz questions (with sources),
    writes them to the question bank.
-   Quiz Master: runs the game loop, selects questions, enforces
    protocol, scores answers.
-   Contestant: answers questions by returning a single letter choice
    (A--F) under a strict protocol.

Primary goals: 1) Make agent-to-agent communication unambiguous. 2) Keep
questions auditable (sources + verification). 3) Run primarily on local
Ollama models.

------------------------------------------------------------------------

## Directory layout (recommended)

quizmaster/ AGENTS.md README.md pyproject.toml src/quizmaster/
orchestrator.py agents/ quiz_master.py contestant.py researcher.py
protocols/ schemas.py prompts.py store/ question_bank.py game_state.py
data/ question_bank.jsonl scripts/ run_quiz.py run_researcher.py
seed_questions.py

------------------------------------------------------------------------

## Core Protocols

### Question Presentation (Quiz Master → Contestant)

QID: `<string>`{=html} CATEGORY: `<string>`{=html} DIFFICULTY: \<int
1-5\> POINTS: `<int>`{=html} QUESTION: `<text>`{=html}

CHOICES: A) `<text>`{=html} B) `<text>`{=html} C) `<text>`{=html} D)
`<text>`{=html} E) `<optional>`{=html} F) `<optional>`{=html}

INSTRUCTIONS: - Reply with EXACTLY one of: A B C D E F (or P if
allowed) - Include QID in your reply

------------------------------------------------------------------------

### Answer Format (Contestant → Quiz Master)

QID: `<string>`{=html} ANSWER: `<single letter A-F or P>`{=html}

Optional: REASON: `<brief explanation>`{=html}

Only QID and ANSWER are used for scoring.

------------------------------------------------------------------------

## Question JSONL Schema

Each line in data/question_bank.jsonl must be a single JSON object:

Required fields: - qid: str - category: str - difficulty: int (1--5) -
points: int - question: str - choices: dict\[A-F -\> str\] (4--6
entries) - answer: str (single letter) - explanation: str - sources:
list of objects {title, url, retrieved} - verified: bool

Optional: - tags: list\[str\] - created_at: ISO timestamp - quality:
dict - notes: str

Rules: - Exactly one correct answer. - Answer letter must exist in
choices. - Choices must be unique. - Factual questions require at least
one reputable source. - Math/logic questions require derivation in
explanation.

------------------------------------------------------------------------

## Agent Contracts

### Researcher

-   Generates valid JSONL Question objects.
-   Provides plausible distractors.
-   Avoids duplicates.
-   Sets difficulty and points consistently.
-   Outputs ONLY JSONL entries in batch mode.

Suggested difficulty/points mapping: 1 → 100 2 → 200 3 → 400 4 → 700 5 →
1000

------------------------------------------------------------------------

### Quiz Master

-   Selects non-repeated, verified questions.
-   Enforces strict formatting.
-   Scores: Correct: +points Wrong: -floor(points \*
    NEGATIVE_SCORING_FACTOR) Pass (P): 0 points (one per game default)
-   Treats malformed answers as incorrect.
-   Never alters stored correct answers.

------------------------------------------------------------------------

### Contestant

-   Outputs exactly: QID: `<qid>`{=html} ANSWER: `<A-F or P>`{=html}
-   Never outputs multiple letters.
-   Never rewrites the question.
-   Optional short REASON allowed.

------------------------------------------------------------------------

## Environment Variables

QUIZMASTER_OLLAMA_HOST (default http://localhost:11434)
QUIZMASTER_MODEL_QUIZMASTER QUIZMASTER_MODEL_CONTESTANT
QUIZMASTER_MODEL_RESEARCHER QUIZMASTER_MAX_QUESTIONS_PER_GAME (default
10) QUIZMASTER_NEGATIVE_SCORING_FACTOR (default 0.5)
QUIZMASTER_ALLOW_PASS (default true)

------------------------------------------------------------------------

## Acceptance Criteria (Milestone 1)

-   Researcher can generate ≥ 50 valid questions.
-   Quiz runs end-to-end with scoring.
-   All agents run using local Ollama.
-   All question records validate against schema.

------------------------------------------------------------------------

End of AGENTS.md
