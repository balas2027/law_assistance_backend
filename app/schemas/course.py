from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.lesson import Lesson

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    lessons: List[Lesson] = []

    model_config = ConfigDict(from_attributes=True)
