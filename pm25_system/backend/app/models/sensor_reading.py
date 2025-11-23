from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    pm25_value = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=True)  # e.g., "Low", "Moderate", "High"

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to alerts
    alerts = relationship("Alert", back_populates="reading")
