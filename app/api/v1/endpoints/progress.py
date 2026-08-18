from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.progress_service import progress_service

router = APIRouter()


@router.post("/lessons/{lesson_id}/complete")
def mark_lesson_completed(lesson_id: int,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)) -> Dict:
    record = progress_service.mark_lesson_completed(db, user_id=current_user.id, lesson_id=lesson_id)
    return {
        "completed": True,
        "completed_at": record.completed_at,
        "lesson_id": record.lesson_id,
        "course_id": record.course_id,
    }


@router.delete("/lessons/{lesson_id}/complete")
def unmark_lesson_completed(lesson_id: int,
                            db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)) -> Dict:
    progress_service.unmark_lesson_completed(db, user_id=current_user.id, lesson_id=lesson_id)
    return {"completed": False, "completed_at": None}


@router.get("/lessons/{lesson_id}/status")
def get_lesson_completion_status(lesson_id: int,
                                 db: Session = Depends(get_db),
                                 current_user: User = Depends(get_current_user)) -> Dict:
    return progress_service.is_lesson_completed(db, user_id=current_user.id, lesson_id=lesson_id)


@router.get("/academy-stats")
def get_academy_stats(db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)) -> Dict:
    return progress_service.get_academy_stats(db, user_id=current_user.id)
