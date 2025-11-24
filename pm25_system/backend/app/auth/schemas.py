<<<<<<< HEAD
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None


=======
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

>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
<<<<<<< HEAD
    role: str

=======
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
<<<<<<< HEAD
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str
=======
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258


class InviteCreate(BaseModel):
    email: EmailStr
    role: str


class InviteOut(BaseModel):
    email: EmailStr
    role: str
<<<<<<< HEAD
    token: str
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True
=======
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258


class InviteAccept(BaseModel):
    token: str
    name: str
    email: EmailStr
    password: str
