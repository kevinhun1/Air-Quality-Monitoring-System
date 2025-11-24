from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import Base, engine
from app.models import user, sensor_reading, alert, invite
import os
from app.auth import hash as hash_utils
from app.auth import utils as auth_utils
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request, Depends, Form, Response
from fastapi.responses import RedirectResponse
import secrets, hashlib
from datetime import datetime, timedelta
from app.auth import deps as auth_deps
from app.models.invite import Invite
from app.database.connection import SessionLocal
from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.jwt import decode_token
import traceback


def _resolve_current_user_from_cookie(request: Request):
    """Safely decode the access_token cookie and return a User or None.
    Uses an explicit SessionLocal session and always closes it.
    """
    token = request.cookies.get('access_token')
    if not token:
        return None
    try:
        payload = decode_token(token)
    except Exception:
        return None

    sub = payload.get('sub') or payload.get('user_id')
    if not sub:
        return None

    db = SessionLocal()
    try:
        # sub may be an email (str) or a user_id (int)
        if isinstance(sub, int):
            user = db.query(User).filter(User.id == sub).first()
        else:
            user = db.query(User).filter(User.email == sub).first()
        return user
    finally:
        db.close()

# Application instance
app = FastAPI(
    title="PM2.5 Monitoring System",
    version="1.0.0"
)

# Templates & static
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# By default we do NOT auto-create tables on import. To enable automatic
# table creation (useful for local development), set the env var
# `DEV_CREATE_TABLES=true` before starting the server. This avoids
# accidental schema changes in production.

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    # Redirect to the canonical home route handled by the home router.
    return RedirectResponse(url='/home')


@app.get("/ui/dashboard")
def ui_dashboard(request: Request, db: Session = Depends(get_db)):
    # Import here to avoid circular imports at module import time
    from app.routers import dashboard as dashboard_router
    summary = dashboard_router.summary(db=db)
    # attempt to resolve current_user from cookie for UI navigation
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse("dashboard.html", {"request": request, "summary": summary, "current_user": current_user})


@app.get('/ui/auth/login')
def ui_login_get(request: Request):
    # pass current_user (if any) to template for nav
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse('login.html', {"request": request, "message": None, "current_user": current_user})


@app.post('/ui/auth/login')
def ui_login_post(request: Request, response: Response, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not hash_utils.verify_password(password, user.password_hash):
        return templates.TemplateResponse('login.html', {"request": request, "message": "Invalid credentials"})

    # If admin — issue JWT and set cookie for UI convenience
    if user.role and user.role.lower() == 'admin':
        token_data = {"sub": user.email, "role": user.role}
        access_token = auth_utils.create_access_token(token_data, expires_delta=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60')))
        # Set httponly cookie
        response = Response(status_code=302)
        response.set_cookie('access_token', access_token, httponly=True, path='/', max_age=60*60)
        response.headers['Location'] = '/ui/dashboard'
        return response

    # Regular user — simple redirect on success
    resp = Response(status_code=302)
    resp.headers['Location'] = '/ui/dashboard'
    return resp


@app.get('/ui/auth/register')
def ui_register_get(request: Request):
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse('register.html', {"request": request, "message": None, "current_user": current_user})


@app.post('/ui/auth/register')
def ui_register_post(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse('register.html', {"request": request, "message": "Email already registered"})
    hashed = hash_utils.hash_password(password)
    user = User(name=name, email=email, password_hash=hashed, role='resident')
    db.add(user)
    db.commit()
    return Response(status_code=302, headers={"Location": "/ui/auth/login"})


@app.get('/ui/auth/invite/accept')
def ui_invite_accept_get(request: Request, token: str = None):
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": None, "current_user": current_user})


@app.post('/ui/auth/invite/accept')
def ui_invite_accept_post(request: Request, token: str = Form(...), name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Call existing API logic for invite acceptance (reuse code from routers.auth.accept_invite)
    import hashlib
    from datetime import datetime
    from app.models.invite import Invite
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invite = db.query(Invite).filter(Invite.token_hash == token_hash).first()
    if not invite:
        return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": "Invite not found"})
    if invite.used:
        return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": "Invite already used"})
    if invite.expires_at < datetime.utcnow():
        return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": "Invite expired"})
    if email.lower() != invite.email.lower():
        return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": "Email does not match invite"})
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse('invite_accept.html', {"request": request, "token": token, "message": "Email already registered"})
    hashed = hash_utils.hash_password(password)
    user = User(name=name, email=email, password_hash=hashed, role=invite.role)
    db.add(user)
    invite.used = True
    db.add(invite)
    db.commit()
    return Response(status_code=302, headers={"Location": "/ui/auth/login"})



@app.get('/ui/auth/logout')
def ui_logout(request: Request):
    resp = RedirectResponse(url='/ui/auth/login')
    resp.delete_cookie('access_token', path='/')
    return resp


@app.get('/ui/auth/invite')
def ui_invite_get(request: Request, current_user: User = Depends(auth_deps.require_role('admin'))):
    return templates.TemplateResponse('invite_create.html', {"request": request, "message": None, "current_user": current_user})


@app.post('/ui/auth/invite')
def ui_invite_post(request: Request, email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(auth_deps.require_role('admin'))):
    # create invite and show token (for dev); in prod email it
    token = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=int(os.getenv('INVITE_TTL_HOURS', '48')))
    invite = Invite(email=email, token_hash=token_hash, role=role, expires_at=expires_at)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return templates.TemplateResponse('invite_create.html', {"request": request, "message": "Invite created", "token": token, "invite": invite, "current_user": current_user})


# include routers (API)
from app.auth.router import router as auth_router
from app.routers import readings as readings_router
from app.routers import dashboard as dashboard_router
from app.routers import crud as crud_router
from app.routers import home as home_router

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(readings_router.router)
app.include_router(dashboard_router.router)
app.include_router(crud_router.router)
app.include_router(home_router.router)

_create_tables = os.getenv("DEV_CREATE_TABLES", "").lower() in ("1", "true", "yes")
if _create_tables:
    Base.metadata.create_all(bind=engine)
