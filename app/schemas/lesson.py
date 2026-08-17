from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class LessonBase(BaseModel):
    title:       str
    content:     Optional[str] = None
    course_id:   int
    status:      str = "draft"
    author_name: Optional[str] = None

class LessonCreate(LessonBase):
    pass

class LessonUpdate(BaseModel):
    title:       Optional[str] = None
    content:     Optional[str] = None
    course_id:   Optional[int] = None
    status:      Optional[str] = None
    author_name: Optional[str] = None

class Lesson(LessonBase):
    id:         int
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

