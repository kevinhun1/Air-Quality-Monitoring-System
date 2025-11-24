from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database.connection import SessionLocal
from app.auth.jwt import decode_token
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _resolve_current_user_from_cookie(request: Request):
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
        if isinstance(sub, int):
            user = db.query(User).filter(User.id == sub).first()
        else:
            user = db.query(User).filter(User.email == sub).first()
        return user
    finally:
        db.close()


@router.get('/home', response_class=HTMLResponse)
def ui_home(request: Request):
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse('landing.html', {"request": request, "current_user": current_user})


@router.get('/', response_class=HTMLResponse)
def ui_root(request: Request):
    # Also serve landing at root when mounted directly (helpful if this router
    # is used standalone). The application's main root will redirect to '/home'.
    current_user = _resolve_current_user_from_cookie(request)
    return templates.TemplateResponse('landing.html', {"request": request, "current_user": current_user})
