from typing import Optional

from quizmaster.clients import OllamaClient, OllamaError
from quizmaster.config import get_model_for_role, get_ollama_host, is_dry_run


class Researcher:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        resolved_model = model or get_model_for_role("researcher")
        self.client = OllamaClient(base_url=base_url or get_ollama_host(), model=resolved_model)

    def generate_question(self) -> str:
        if is_dry_run() or not self.client.model:
            return "Researcher dry run: no question generated."
        prompt = "Draft a multiple-choice trivia question with 4 choices."
        try:
            response = self.client.generate(prompt)
        except (OllamaError, ValueError) as exc:
            return f"Researcher error: {exc}"
        return response.get("response", "").strip() or "Researcher generated no output."
