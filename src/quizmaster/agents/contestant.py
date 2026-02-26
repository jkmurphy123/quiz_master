from typing import Optional

from quizmaster.clients import OllamaClient, OllamaError
from quizmaster.config import get_model_for_role, get_ollama_host, is_dry_run


class Contestant:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        resolved_model = model or get_model_for_role("contestant")
        self.client = OllamaClient(base_url=base_url or get_ollama_host(), model=resolved_model)

    def answer(self, question_block: str) -> str:
        if is_dry_run() or not self.client.model:
            return "QID: UNKNOWN\nANSWER: A"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a quiz contestant. Respond strictly with:\n"
                    "QID: <qid>\nANSWER: <A-F or P>\nNo extra text."
                ),
            },
            {"role": "user", "content": question_block},
        ]
        try:
            response = self.client.chat(messages)
        except (OllamaError, ValueError) as exc:
            return f"QID: UNKNOWN\nANSWER: A\nREASON: {exc}"
        content = response.get("message", {}).get("content", "").strip()
        return content or "QID: UNKNOWN\nANSWER: A"
