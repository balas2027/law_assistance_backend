from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import get_password_hash
from app.services.quiz_service import quiz_service

router = APIRouter()


@router.get("/me")
def read_user_me(current_user: User = Depends(get_current_user)) -> dict:
    from app.services.auth_service import auth_service
    return auth_service.to_user_out(current_user)


@router.put("/me")
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.services.auth_service import auth_service

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        current_user.hashed_password = get_password_hash(update_data.pop("password"))
    if "full_name" in update_data and update_data["full_name"] is not None:
        current_user.full_name = update_data["full_name"]

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return auth_service.to_user_out(current_user)


@router.get("/me/stats")
def read_user_stats(db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)) -> dict:
    return quiz_service.get_user_stats(db, user_id=current_user.id)


@router.get("/me/topics/progress")
def read_user_topic_progress(db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)) -> List[dict]:
    return quiz_service.get_user_topic_progress(db, user_id=current_user.id)


@router.get("/me/attempts")
def read_user_attempts(quiz_id: Optional[int] = None, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)) -> List[dict]:
    return quiz_service.get_user_attempts(db, user_id=current_user.id, quiz_id=quiz_id)


@router.get("/me/quiz-progress")
def read_user_quiz_progress(db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)) -> List[dict]:
    return quiz_service.get_user_quiz_progress(db, user_id=current_user.id)