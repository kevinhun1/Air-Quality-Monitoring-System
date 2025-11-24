from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=False)

    alert_type = Column(String(50), nullable=False)      # SMS, Telegram, Dashboard
    message = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="alerts")
    reading = relationship("SensorReading", back_populates="alerts")
