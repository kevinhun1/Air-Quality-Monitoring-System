from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.connection import SessionLocal
from app.models.user import User
from app.auth import schemas, utils, deps

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.UserOut)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    # allow open registration only for residents
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = utils.hash_password(payload.password)
    user = User(name=payload.name, email=payload.email, password_hash=hashed, role="resident")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: dict, db: Session = Depends(get_db)):
    """
    This endpoint accepts JSON: {"email": "...", "password": "..."}
    (Using OAuth2PasswordRequestForm would require form-encoded body.)
    """
    email = form_data.get("email")
    password = form_data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = db.query(User).filter(User.email == email).first()
    if not user or not utils.verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

    token_data = {"user_id": user.id, "role": user.role}
    access_token = utils.create_access_token(token_data, expires_delta=int(utils.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# Example admin-only route to create admin/health worker (optional)
@router.post("/create_user_admin", response_model=schemas.UserOut)
def create_user_admin(payload: schemas.UserCreate, current_user = Depends(deps.require_role("admin")), db: Session = Depends(get_db)):
    # current_user is guaranteed to be admin by dependency
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = utils.hash_password(payload.password)
    # expect payload.role passed in real world; here use 'health_worker' or 'admin'
    # to keep the endpoint safe, you might extend payload to include role.
    user = User(name=payload.name, email=payload.email, password_hash=hashed, role="health_worker")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
