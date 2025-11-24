from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import Optional

from app.database.connection import SessionLocal
from app.models.user import User

load_dotenv()
# allow missing Authorization header (auto_error=False) so we can fall back to cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # If token not provided via Authorization header, try cookie fallback
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    # Support tokens that include either user_id or sub (email)
    user = None
    user_id = payload.get("user_id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    else:
        # some tokens encode 'sub' as the user's email
        sub = payload.get("sub")
        if sub:
            user = db.query(User).filter(User.email == sub).first()

    if user is None:
        raise credentials_exception

    return user


def require_role(role: str):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return current_user
    return role_checker
