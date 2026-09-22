"""
Pydantic schemas used for request/response validation.
Keep these in sync with whatever your TypeScript UI's `types.ts` expects.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated conversation id")
    message: str = Field(..., min_length=1)
    language: str = Field(default="en", description="ISO code, e.g. 'en', 'hi', 'ta'")
    # Optional: if the UI already has the user's location, pass it to skip geocoding
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str                     # "current_weather" | "forecast" | "alerts" | "general"
    location_resolved: Optional[str] = None
    data: Optional[dict] = None     # raw structured weather data behind the reply


# ---------- Weather ----------

class CurrentWeatherResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    humidity: int
    wind_speed_ms: float
    condition: str
    description: str
    observed_at: datetime


class ForecastEntry(BaseModel):
    datetime: datetime
    temperature_c: float
    condition: str
    description: str
    pop: float = Field(..., description="Probability of precipitation, 0-1")


class ForecastResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    daily: List[ForecastEntry]


class AlertOut(BaseModel):
    event: str
    severity: Optional[str]
    description: Optional[str]
    source: str
    issued_at: datetime
    expires_at: Optional[datetime]


class AlertsResponse(BaseModel):
    location: str
    alerts: List[AlertOut]
