from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.sensor_reading import SensorReading
from app.routers.schemas import SensorReadingCreate

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
    reading = SensorReading(
        pm25_value=data.pm25_value,
        timestamp=data.timestamp,
        risk_level=None  # ML model will fill this later
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {"message": "Reading stored successfully", "reading_id": reading.id}
