from typing import Generator
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth_service import auth_service

security = HTTPBearer()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    return auth_service.get_current_user(db, credentials.credentials)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    is_admin = current_user.is_superuser or (
        current_user.user_type and current_user.user_type.code in ("admin", "law_professional")
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user