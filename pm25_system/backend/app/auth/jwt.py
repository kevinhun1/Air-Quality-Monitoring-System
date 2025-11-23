from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

# Read ACCESS_TOKEN_EXPIRE_MINUTES robustly: treat missing/empty/invalid values as default 60
_expire_env = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_env) if str(_expire_env).strip() != "" else 60
except (TypeError, ValueError):
    ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise
