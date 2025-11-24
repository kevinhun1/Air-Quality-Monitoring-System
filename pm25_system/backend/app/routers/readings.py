from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
<<<<<<< HEAD

from app.database.connection import SessionLocal
from app.models.sensor_reading import SensorReading
from app.routers.schemas import SensorReadingCreate
=======
from app.database.connection import SessionLocal
from app.models.sensor_reading import SensorReading
from app.routers.schemas import SensorReadingCreate
from app.ml.predictor import classify_pm25
from app.models.user import User
from app.models.alert import Alert
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258

router = APIRouter(
    prefix="/api/readings",
    tags=["Sensor Readings"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def ingest_reading(data: SensorReadingCreate, db: Session = Depends(get_db)):
<<<<<<< HEAD
    reading = SensorReading(
        pm25_value=data.pm25_value,
        timestamp=data.timestamp,
        risk_level=None  # ML model will fill this later
=======
    
    risk = classify_pm25(data.pm25_value)  # ML Classification

    reading = SensorReading(
        pm25_value=data.pm25_value,
        timestamp=data.timestamp,
        risk_level=risk
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

<<<<<<< HEAD
    return {"message": "Reading stored successfully", "reading_id": reading.id}
=======
    # Alert triggering rules: map risk levels to roles that should be alerted.
    ALERT_RULES = {
        "Unhealthy": ["health_worker", "admin"],
        "Very Unhealthy": ["health_worker", "admin", "resident"],
        "Hazardous": ["health_worker", "admin", "resident"],
    }

    roles_to_alert = ALERT_RULES.get(risk, [])
    if roles_to_alert:
        # find users with these roles
        users = db.query(User).filter(User.role.in_(roles_to_alert)).all()
        message = f"PM2.5 reading {reading.pm25_value} detected (Risk: {risk})."
        for u in users:
            alert = Alert(user_id=u.id, reading_id=reading.id, alert_type="Dashboard", message=message)
            db.add(alert)
        db.commit()

    return {
        "message": "Reading stored successfully",
        "reading_id": reading.id,
        "risk_level": risk
    }
>>>>>>> b229d0647d56508b389d6ee36e830a7999909258
