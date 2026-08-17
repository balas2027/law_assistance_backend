from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut
from app.services.auth_service import auth_service

router = APIRouter()


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)) -> dict:
    return auth_service.to_user_out(current_user)