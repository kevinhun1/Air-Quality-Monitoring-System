from fastapi import Depends, HTTPException, status, Request
<<<<<<< HEAD
from sqlalchemy.orm import Session
from typing import Generator, Optional
from app.database.connection import SessionLocal
from app.models.user import User
from app.auth import hash as hash_utils
from app.auth import jwt as jwt_utils
import base64


def get_db() -> Generator[Session, None, None]:
=======
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
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


<<<<<<< HEAD
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

=======
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
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
    return role_checker
