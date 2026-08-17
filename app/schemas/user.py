from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

VALID_USER_TYPES = {"common_man", "admin"}


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    user_type: str = "common_man"
    is_active: Optional[bool] = True
    is_superuser: bool = False

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        if v not in VALID_USER_TYPES:
            raise ValueError(f"user_type must be one of {sorted(VALID_USER_TYPES)}")
        return v


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int
    user_type_id: int
    role_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: EmailStr
    user_type: str
    user_type_id: int
    role_name: str
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)