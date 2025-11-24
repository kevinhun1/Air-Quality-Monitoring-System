from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.models.sensor_reading import SensorReading
from app.models.alert import Alert

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/summary")
def summary(hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return summary statistics for the last `hours` hours."""
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)

    readings = db.query(SensorReading).filter(SensorReading.timestamp >= start).all()
    total = len(readings)
    if total == 0:
        return {
            "period_hours": hours,
            "total_readings": 0,
            "avg_pm25": None,
            "min_pm25": None,
            "max_pm25": None,
            "counts_by_risk": {},
            "alerts_count": 0,
        }

    vals = [r.pm25_value for r in readings]
    risks = {}
    for r in readings:
        risks[r.risk_level] = risks.get(r.risk_level, 0) + 1

    alerts_count = db.query(Alert).filter(Alert.created_at >= start).count()

    return {
        "period_hours": hours,
        "total_readings": total,
        "avg_pm25": sum(vals) / total,
        "min_pm25": min(vals),
        "max_pm25": max(vals),
        "counts_by_risk": risks,
        "alerts_count": alerts_count,
    }


@router.get("/history")
def history(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=1000), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Paginated reading history ordered by newest first."""
    query = db.query(SensorReading).order_by(SensorReading.timestamp.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {"id": r.id, "pm25_value": r.pm25_value, "risk_level": r.risk_level, "timestamp": r.timestamp.isoformat()}
        for r in items
    ]
    return {"page": page, "page_size": page_size, "total": total, "items": data}


@router.get("/chart")
def chart(hours: int = Query(24, ge=1, le=720), interval_minutes: int = Query(60, ge=1, le=1440), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return time-bucketed averages for charting over the last `hours` hours.
    `interval_minutes` defines bucket size in minutes.
    """
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    readings = db.query(SensorReading).filter(SensorReading.timestamp >= start).all()

    # prepare buckets
    total_minutes = hours * 60
    num_buckets = (total_minutes + interval_minutes - 1) // interval_minutes
    buckets = [ {"start": (start + timedelta(minutes=i * interval_minutes)).isoformat(), "avg_pm25": None, "count": 0} for i in range(num_buckets) ]

    if readings:
        # bucket readings
        for r in readings:
            # normalize timestamp to naive UTC
            ts = r.timestamp
            if ts.tzinfo is not None:
                ts = ts.astimezone(tz=None).replace(tzinfo=None)
            delta = ts - start
            idx = int(delta.total_seconds() // (interval_minutes * 60))
            if 0 <= idx < num_buckets:
                b = buckets[idx]
                if b["avg_pm25"] is None:
                    b["avg_pm25"] = r.pm25_value
                    b["count"] = 1
                else:
                    # running average
                    b["avg_pm25"] = (b["avg_pm25"] * b["count"] + r.pm25_value) / (b["count"] + 1)
                    b["count"] += 1

    return {"start": start.isoformat(), "end": now.isoformat(), "interval_minutes": interval_minutes, "buckets": buckets}
