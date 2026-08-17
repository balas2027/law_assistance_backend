from typing import Optional
from sqlalchemy.orm import Session
from app.models.user_type import UserType


class UserTypeRepository:
    def get(self, db: Session, id: int) -> Optional[UserType]:
        return db.query(UserType).filter(UserType.id == id).first()

    def get_by_code(self, db: Session, *, code: str) -> Optional[UserType]:
        return db.query(UserType).filter(UserType.code == code).first()


user_type_repository = UserTypeRepository()