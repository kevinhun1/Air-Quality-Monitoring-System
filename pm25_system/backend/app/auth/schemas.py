from pydantic import EmailStr
from typing import Optional
from datetime import datetime

from app.utils.pydantic_compat import OrmBase as BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str


class InviteCreate(BaseModel):
    email: EmailStr
    role: str


class InviteOut(BaseModel):
    email: EmailStr
    role: str
    token: Optional[str] = None
    expires_at: Optional[datetime] = None


class InviteAccept(BaseModel):
    token: str
    name: str
    email: EmailStr
    password: str
