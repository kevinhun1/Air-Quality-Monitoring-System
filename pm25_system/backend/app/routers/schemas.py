from pydantic import BaseModel
from datetime import datetime

class SensorReadingCreate(BaseModel):
    pm25_value: float
    timestamp: datetime 
    
