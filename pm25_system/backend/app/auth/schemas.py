from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class InviteCreate(BaseModel):
    email: EmailStr
    role: str


class InviteOut(BaseModel):
    email: EmailStr
    role: str
    token: str
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True


class InviteAccept(BaseModel):
    token: str
    name: str
    email: EmailStr
    password: str
