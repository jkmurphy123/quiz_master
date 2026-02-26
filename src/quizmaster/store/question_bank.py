import json
from pathlib import Path

class QuestionBank:
    def __init__(self, path: str):
        self.path = Path(path)

    def append(self, question: dict):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(question) + "\n")
