"""
Database models for WeatherGPT.

- ChatMessage: stores every turn of every conversation (for history + analytics).
- WeatherAlertLog: caches alerts we've fetched/dispatched, useful for the
  "early warning dissemination" requirement and to avoid re-notifying.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)


class WeatherAlertLog(Base):
    __tablename__ = "weather_alert_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    event = Column(String, nullable=False)          # e.g. "Cyclone Warning"
    severity = Column(String, nullable=True)         # e.g. "Severe"
    description = Column(Text, nullable=True)
    source = Column(String, default="OpenWeatherMap")
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
