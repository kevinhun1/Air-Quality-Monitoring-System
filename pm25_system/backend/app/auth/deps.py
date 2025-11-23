from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Generator, Optional
from app.database.connection import SessionLocal
from app.models.user import User
from app.auth import hash as hash_utils
from app.auth import jwt as jwt_utils
import base64


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not hash_utils.verify_password(password, user.password_hash):
        return None
    return user


def _credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Basic, Bearer"},
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Support either Bearer JWTs or Basic auth (email:password) via Authorization header.
    Bearer: validates JWT and loads user by `sub` (email).
    Basic: decodes credentials and verifies password against DB.
    """
    auth: Optional[str] = request.headers.get("Authorization")
    if not auth:
        raise _credentials_exception()

    # Bearer token
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt_utils.decode_token(token)
            email: str = payload.get("sub") or payload.get("email")
            if email is None:
                raise _credentials_exception()
        except Exception:
            raise _credentials_exception()
        user = get_user_by_email(db, email)
        if user is None:
            raise _credentials_exception()
        return user

    # Basic auth
    if auth.lower().startswith("basic "):
        try:
            b64 = auth.split(" ", 1)[1]
            decoded = base64.b64decode(b64).decode()
            email, password = decoded.split(":", 1)
        except Exception:
            raise _credentials_exception()
        user = authenticate_user(db, email, password)
        if not user:
            raise _credentials_exception()
        return user

    raise _credentials_exception()


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return current_user

    return role_checker
