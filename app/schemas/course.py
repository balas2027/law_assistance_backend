from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.lesson import Lesson

class CourseBase(BaseModel):
    title:       str
    description: Optional[str] = None
    status:      str = "draft"

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    status:      Optional[str] = None

class Course(CourseBase):
    id:         int
    lessons:    List[Lesson] = []
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

