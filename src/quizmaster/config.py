import os
from typing import Optional


def get_ollama_host() -> str:
    return os.getenv("QUIZMASTER_OLLAMA_HOST", "http://localhost:11434")


def get_model_for_role(role: str) -> Optional[str]:
    role_key = role.strip().lower()
    if role_key == "quiz_master":
        return os.getenv("QUIZMASTER_MODEL_QUIZMASTER")
    if role_key == "contestant":
        return os.getenv("QUIZMASTER_MODEL_CONTESTANT")
    if role_key == "researcher":
        return os.getenv("QUIZMASTER_MODEL_RESEARCHER")
    return None


def is_dry_run() -> bool:
    return os.getenv("QUIZMASTER_DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
