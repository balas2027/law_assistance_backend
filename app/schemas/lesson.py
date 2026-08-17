from typing import Optional
from pydantic import BaseModel, ConfigDict

class LessonBase(BaseModel):
    title: str
    content: Optional[str] = None
    course_id: int

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
