from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict
import secrets, hashlib
from app.auth import schemas, hash as hash_utils, jwt as jwt_utils, deps
from app.models.user import User
from app.models.invite import Invite
from app.database.connection import SessionLocal

INVITE_TTL_HOURS = 48

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Prevent public registration as admin — use invite flow
    if user_in.role and user_in.role.lower() == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot register as admin. Request an invite.")

    hashed = hash_utils.hash_password(user_in.password)
    user = User(name=user_in.name, email=user_in.email, password_hash=hashed, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
    user = deps.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    # If user is an admin we continue to issue a JWT (admins use token flow).
    if user.role and user.role.lower() == "admin":
        token_data = {"sub": user.email, "role": user.role}
        access_token_expires = timedelta(minutes=60)
        access_token = jwt_utils.create_access_token(data=token_data, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}

    # For normal users we do not issue tokens — login success is sufficient.
    return {"detail": "Login successful"}


@router.post("/invite", response_model=schemas.InviteOut)
def create_invite(invite_in: schemas.InviteCreate, current_user: User = Depends(deps.require_role('admin')), db: Session = Depends(deps.get_db)):
    # Only admins can create invites
    # generate secure token and store its hash
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=INVITE_TTL_HOURS)
    invite = Invite(email=invite_in.email, token_hash=token_hash, role=invite_in.role, expires_at=expires_at)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    # In production, email the `token` to invitee. For now return token in response so tests/dev can use it.
    return {"email": invite.email, "role": invite.role, "token": token, "expires_at": invite.expires_at}


@router.post("/invite/accept", response_model=schemas.UserOut)
def accept_invite(data: schemas.InviteAccept, db: Session = Depends(deps.get_db)):
    # Validate invite token
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    invite = db.query(Invite).filter(Invite.token_hash == token_hash).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")
    # Ensure the email matches (optional)
    if data.email.lower() != invite.email.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite email mismatch")
    # Create user with role from invite
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed = hash_utils.hash_password(data.password)
    user = User(name=data.name, email=data.email, password_hash=hashed, role=invite.role)
    db.add(user)
    invite.used = True
    db.add(invite)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: User = Depends(deps.get_current_user)):
    return current_user
