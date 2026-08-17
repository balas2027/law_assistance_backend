from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class QuizBase(BaseModel):
    title: str
    questions: List[Dict[str, Any]]
    lesson_id: Optional[int] = None

class QuizCreate(QuizBase):
    pass

class Quiz(QuizBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
