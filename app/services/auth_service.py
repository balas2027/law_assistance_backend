from typing import Tuple
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.repositories.user_type_repository import user_type_repository
from app.schemas.user import UserCreate


class AuthService:
    def signup(self, db: Session, obj_in: UserCreate) -> Tuple[User, str]:
        if user_repository.get_by_email(db, email=obj_in.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user_type = user_type_repository.get_by_code(db, code=obj_in.user_type)
        if not user_type:
            raise HTTPException(status_code=400, detail="Invalid user type")
        user = user_repository.create(db, obj_in=obj_in, user_type_id=user_type.id)
        token = create_access_token(user.id)
        return user, token

    def login(
        self, db: Session, *, email: str, password: str, user_type: str
    ) -> Tuple[User, str]:
        user_type_obj = user_type_repository.get_by_code(db, code=user_type)
        if not user_type_obj:
            raise HTTPException(status_code=400, detail="Invalid user type")
        user = user_repository.authenticate(
            db, email=email, password=password, user_type_id=user_type_obj.id
        )
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Incorrect email, password, or account type",
            )
        token = create_access_token(user.id)
        return user, token

    def get_current_user(self, db: Session, token: str) -> User:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = int(payload.get("sub"))
        except (JWTError, TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")
        user = user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    @staticmethod
    def to_user_out(user: User) -> dict:
        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "user_type": user.user_type.code if user.user_type else None,
            "user_type_id": user.user_type_id,
            "role_name": user.user_type.name if user.user_type else None,
            "is_superuser": user.is_superuser,
        }


auth_service = AuthService()