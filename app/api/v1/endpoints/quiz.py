from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.quiz_attempt import QuizAttempt
from app.schemas.quiz import QuizPublic
from app.schemas.analytics import (
    QuizAttemptOut,
    QuizAnswerSubmit,
    QuizCompleteOut,
)
from app.services.quiz_service import quiz_service

router = APIRouter()


@router.get("", response_model=List[QuizPublic])
def list_quizzes(topic_id: Optional[int] = None, skip: int = 0, limit: int = 50,
                 db: Session = Depends(get_db)) -> list:
    return quiz_service.list_public_quizzes(db, topic_id=topic_id, skip=skip, limit=limit)


@router.get("/{quiz_id}", response_model=QuizPublic)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)) -> QuizPublic:
    from app.repositories.quiz_repository import quiz_repository
    quiz = quiz_repository.get_with_questions(db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.status != "published":
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz_service.to_public(db, quiz)


@router.post("/{quiz_id}/attempts", response_model=QuizAttemptOut)
def start_attempt(quiz_id: int, db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)) -> QuizAttempt:
    return quiz_service.start_attempt(db, user_id=current.id, quiz_id=quiz_id)


@router.post("/attempts/{attempt_id}/answers", response_model=dict)
def submit_answer(attempt_id: int, payload: QuizAnswerSubmit,
                  db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)) -> dict:
    answer = quiz_service.submit_answer(
        db, user_id=current.id, attempt_id=attempt_id,
        question_id=payload.question_id, selected_option_id=payload.selected_option_id,
    )
    return {
        "question_id": answer.question_id,
        "is_correct": answer.is_correct,
        "points_earned": answer.points_earned,
    }


@router.post("/attempts/{attempt_id}/complete", response_model=QuizCompleteOut)
def complete_attempt(attempt_id: int, time_taken_sec: Optional[int] = None,
                     db: Session = Depends(get_db),
                     current: User = Depends(get_current_user)) -> QuizCompleteOut:
    return quiz_service.complete_attempt(
        db, user_id=current.id, attempt_id=attempt_id, time_taken_sec=time_taken_sec,
    )