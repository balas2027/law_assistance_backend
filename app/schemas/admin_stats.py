from typing import Dict, Optional
from pydantic import BaseModel


class AdminStats(BaseModel):
    total_users:         int
    total_lessons:       int
    total_courses:       int
    total_quizzes:       int
    published_quizzes:   int = 0
    total_attempts:      int = 0
    attendees:           int = 0
    users_by_type:       Dict[str, int]