from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class WeatherAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Location
    latitude: float
    longitude: float
    region_name: str

    event_type: str
    severity: str
    value: float

    is_notified: bool = Field(default=False)


class SatelliteLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str
