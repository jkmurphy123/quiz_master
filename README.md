# QuizMaster

A 3-agent quiz system:
- Researcher: builds the question bank
- Quiz Master: runs the game
- Contestant: answers questions

See AGENTS.md for full protocol definitions.

## Ollama Setup

Set the Ollama host (default is `http://localhost:11434`):

```bash
export QUIZMASTER_OLLAMA_HOST=http://localhost:11434
```

Set role-specific models:

```bash
export QUIZMASTER_MODEL_QUIZMASTER=qwen2.5
export QUIZMASTER_MODEL_CONTESTANT=qwen2.5
export QUIZMASTER_MODEL_RESEARCHER=qwen2.5
```

Start Ollama and pull a model:

```bash
ollama serve
ollama pull qwen2.5
```

Smoke test:

```bash
python -m quizmaster.orchestrator
```
