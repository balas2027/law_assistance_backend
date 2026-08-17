from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.topic import TopicOut


class QuestionOptionBase(BaseModel):
    option_key: str
    text: str
    is_correct: bool = False


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionOut(QuestionOptionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    scenario: Optional[str] = None
    explanation: Optional[str] = None
    points: int = 10
    sort_order: int = 0


class QuestionCreate(QuestionBase):
    options: List[QuestionOptionCreate] = []


class QuestionOut(QuestionBase):
    id: int
    options: List[QuestionOptionOut] = []
    model_config = ConfigDict(from_attributes=True)


class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    topic_id: Optional[int] = None
    difficulty: str = "beginner"
    xp_per_question: int = 10
    max_lives: int = 3
    time_limit_sec: Optional[int] = None
    status: str = "draft"


class QuizCreate(QuizBase):
    questions: List[QuestionCreate] = []


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic_id: Optional[int] = None
    difficulty: Optional[str] = None
    xp_per_question: Optional[int] = None
    max_lives: Optional[int] = None
    time_limit_sec: Optional[int] = None
    status: Optional[str] = None


class QuizOut(QuizBase):
    id: int
    topic: Optional[TopicOut] = None
    questions: List[QuestionOut] = []
    created_by: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QuizPublic(BaseModel):
    """User-facing quiz — correct answers stripped."""
    id: int
    title: str
    description: Optional[str] = None
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    difficulty: str
    xp_per_question: int
    max_lives: int
    time_limit_sec: Optional[int] = None
    questions: List[dict] = []
    model_config = ConfigDict(from_attributes=True)