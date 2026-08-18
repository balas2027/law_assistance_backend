from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.lesson_completion import LessonCompletion


class LessonCompletionRepository(CRUDBase[LessonCompletion, dict, dict]):
    def get_by_user_lesson(self, db: Session, *, user_id: int, lesson_id: int) -> Optional[LessonCompletion]:
        return db.query(LessonCompletion).filter(
            LessonCompletion.user_id == user_id,
            LessonCompletion.lesson_id == lesson_id,
        ).first()

    def list_for_user(self, db: Session, *, user_id: int) -> List[LessonCompletion]:
        return db.query(LessonCompletion).filter(LessonCompletion.user_id == user_id).all()


lesson_completion_repository = LessonCompletionRepository(LessonCompletion)