from pydantic import BaseModel
from typing import Dict, List

class Source(BaseModel):
    title: str
    url: str
    retrieved: str

class Question(BaseModel):
    qid: str
    category: str
    difficulty: int
    points: int
    question: str
    choices: Dict[str, str]
    answer: str
    explanation: str
    sources: List[Source]
    verified: bool
