from pydantic import BaseModel, EmailStr
from app.schemas.user import UserOut


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str


class TokenPayload(BaseModel):
    sub: str = None