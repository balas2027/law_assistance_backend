from typing import List
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


class LessonRepository(CRUDBase[Lesson, LessonCreate, LessonUpdate]):
    def get_by_course(self, db: Session, *, course_id: int) -> List[Lesson]:
        return db.query(Lesson).filter(Lesson.course_id == course_id).all()


lesson_repository = LessonRepository(Lesson)
