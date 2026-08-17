from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(obj_in: UserCreate, db: Session = Depends(get_db)) -> Token:
    user, access_token = auth_service.signup(db, obj_in)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=auth_service.to_user_out(user),
    )


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user, access_token = auth_service.login(
        db, email=req.email, password=req.password
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=auth_service.to_user_out(user),
    )