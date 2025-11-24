from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert

router = APIRouter(prefix="/crud", tags=["CRUD"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


### Users ###


@router.get("/users", response_model=List[dict])
def list_users(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000), db: Session = Depends(get_db)):
    q = db.query(User).order_by(User.id.asc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in items]


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role}


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: dict, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    # only allow updating name, email, role
    if "email" in payload and payload["email"] != u.email:
        exists = db.query(User).filter(User.email == payload["email"]).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")
        u.email = payload["email"]
    if "name" in payload:
        u.name = payload["name"]
    if "role" in payload:
        u.role = payload["role"]
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
    return None


### Readings ###


@router.get("/readings", response_model=List[dict])
def list_readings(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000), db: Session = Depends(get_db)):
    q = db.query(SensorReading).order_by(SensorReading.timestamp.desc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return [{"id": r.id, "pm25_value": r.pm25_value, "risk_level": r.risk_level, "timestamp": r.timestamp.isoformat()} for r in items]


@router.get("/readings/{reading_id}")
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    r = db.query(SensorReading).get(reading_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reading not found")
    return {"id": r.id, "pm25_value": r.pm25_value, "risk_level": r.risk_level, "timestamp": r.timestamp.isoformat()}


@router.delete("/readings/{reading_id}", status_code=204)
def delete_reading(reading_id: int, db: Session = Depends(get_db)):
    r = db.query(SensorReading).get(reading_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reading not found")
    db.delete(r)
    db.commit()
    return None


### Alerts ###


@router.get("/alerts", response_model=List[dict])
def list_alerts(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000), db: Session = Depends(get_db)):
    q = db.query(Alert).order_by(Alert.created_at.desc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return [{"id": a.id, "user_id": a.user_id, "reading_id": a.reading_id, "alert_type": a.alert_type, "message": a.message, "created_at": a.created_at.isoformat()} for a in items]


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": a.id, "user_id": a.user_id, "reading_id": a.reading_id, "alert_type": a.alert_type, "message": a.message, "created_at": a.created_at.isoformat()}


@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(a)
    db.commit()
    return None
