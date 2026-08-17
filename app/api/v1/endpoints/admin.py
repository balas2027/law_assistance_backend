from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.user import User
from app.schemas.admin_stats import AdminStats
from app.schemas.user import UserOut
from app.schemas.analytics import QuizAnalyticsOut, TopicAnalyticsOut
from app.services.admin_service import admin_service
from app.repositories.user_repository import user_repository
from app.services.auth_service import auth_service

router = APIRouter()


@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AdminStats:
    return admin_service.get_dashboard_stats(db)


@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> list:
    users = user_repository.get_multi(db, skip=skip, limit=limit)
    return [auth_service.to_user_out(u) for u in users]


@router.get("/quizzes/{quiz_id}/analytics", response_model=QuizAnalyticsOut)
def get_quiz_analytics(
    quiz_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> QuizAnalyticsOut:
    try:
        return admin_service.get_quiz_analytics(db, quiz_id=quiz_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Quiz not found")


@router.get("/topics/{topic_id}/analytics", response_model=TopicAnalyticsOut)
def get_topic_analytics(
    topic_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> TopicAnalyticsOut:
    try:
        return admin_service.get_topic_analytics(db, topic_id=topic_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Topic not found")