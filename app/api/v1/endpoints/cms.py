from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.user import User
from app.models.topic import Topic
from app.models.quiz import Quiz
from app.repositories.topic_repository import topic_repository
from app.repositories.quiz_repository import quiz_repository
from app.schemas.topic import TopicCreate, TopicUpdate, TopicOut
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizOut
from app.services.quiz_service import quiz_service

router = APIRouter()


# ── Topics ─────────────────────────────────────────────────────────────────────

@router.get("/topics", response_model=List[TopicOut])
def list_topics(db: Session = Depends(get_db)) -> list:
    return topic_repository.get_multi(db, limit=200)


@router.post("/topics", response_model=TopicOut)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db),
                 _: User = Depends(get_current_admin)) -> Topic:
    return topic_repository.create(db, obj_in=payload)


@router.put("/topics/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db),
                 _: User = Depends(get_current_admin)) -> Topic:
    topic = topic_repository.get(db, id=topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic_repository.update(db, db_obj=topic, obj_in=payload)


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db),
                 _: User = Depends(get_current_admin)) -> dict:
    if not topic_repository.get(db, id=topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")
    topic_repository.remove(db, id=topic_id)
    return {"ok": True}


# ── Quizzes (CMS, admin) ──────────────────────────────────────────────────────

@router.get("/quizzes", response_model=List[QuizOut])
def list_all_quizzes(status: Optional[str] = None, skip: int = 0, limit: int = 100,
                     db: Session = Depends(get_db)) -> list:
    q = db.query(Quiz).order_by(Quiz.created_at.desc()).offset(skip).limit(limit)
    if status:
        q = q.filter(Quiz.status == status)
    return q.all()


@router.post("/quizzes", response_model=QuizOut)
def create_quiz(payload: QuizCreate, db: Session = Depends(get_db),
                current: User = Depends(get_current_admin)) -> Quiz:
    return quiz_service.create_quiz(db, payload=payload, created_by=current.id)


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)) -> Quiz:
    quiz = quiz_repository.get_with_questions(db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.put("/quizzes/{quiz_id}", response_model=QuizOut)
def update_quiz(quiz_id: int, payload: QuizUpdate, db: Session = Depends(get_db),
                _: User = Depends(get_current_admin)) -> Quiz:
    quiz = quiz_repository.get(db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz_service.update_quiz(db, db_obj=quiz, payload=payload)


@router.delete("/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db),
                _: User = Depends(get_current_admin)) -> dict:
    if not quiz_repository.get(db, id=quiz_id):
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz_repository.remove(db, id=quiz_id)
    return {"ok": True}


@router.post("/quizzes/{quiz_id}/publish", response_model=QuizOut)
def publish_quiz(quiz_id: int, db: Session = Depends(get_db),
                 _: User = Depends(get_current_admin)) -> Quiz:
    quiz = quiz_repository.get(db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz_service.set_quiz_status(db, db_obj=quiz, status="published")


@router.post("/quizzes/{quiz_id}/unpublish", response_model=QuizOut)
def unpublish_quiz(quiz_id: int, db: Session = Depends(get_db),
                   _: User = Depends(get_current_admin)) -> Quiz:
    quiz = quiz_repository.get(db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz_service.set_quiz_status(db, db_obj=quiz, status="draft")