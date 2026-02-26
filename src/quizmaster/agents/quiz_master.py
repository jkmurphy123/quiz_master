from typing import Optional

from quizmaster.clients import OllamaClient, OllamaError
from quizmaster.config import get_model_for_role, get_ollama_host, is_dry_run


class QuizMaster:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        resolved_model = model or get_model_for_role("quiz_master")
        self.client = OllamaClient(base_url=base_url or get_ollama_host(), model=resolved_model)

    def rephrase_question_for_stage_direction(self, question_text: str) -> str:
        if is_dry_run() or not self.client.model:
            return question_text
        messages = [
            {"role": "system", "content": "You are the Quiz Master. Keep outputs short."},
            {"role": "user", "content": f"Rephrase for hosting: {question_text}"},
        ]
        try:
            response = self.client.chat(messages)
        except (OllamaError, ValueError) as exc:
            return f"(ollama error: {exc})"
        return response.get("message", {}).get("content", "").strip() or question_text

    def run_game(self):
        print("QuizMaster running game loop...")
