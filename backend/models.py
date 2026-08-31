import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from backend.database import Base

# SQLAlchemy Models
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(255), nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), default="preference")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    time_of_day = Column(String(50), nullable=True)
    frequency = Column(Integer, default=1)
    last_executed = Column(DateTime, default=datetime.datetime.utcnow)
    auto_enabled = Column(Boolean, default=False)

class VisualMemory(Base):
    __tablename__ = "visual_memories"

    id = Column(Integer, primary_key=True, index=True)
    object_name = Column(String(100), index=True, nullable=False)
    location_context = Column(String(255), nullable=False)
    room = Column(String(100), default="room")
    spatial_relationship = Column(String(255), nullable=True)
    confidence = Column(Float, default=0.9)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    observation_count = Column(Integer, default=1)
    is_user_saved = Column(Boolean, default=False)

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Pydantic Schemas
class MessageCreate(BaseModel):
    text: str
    is_voice: bool = False
    source: str = "chat"

class ReminderCreate(BaseModel):
    text: str
    time_str: str

class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    reminder_time: datetime.datetime
    is_active: bool
    is_completed: bool

class MemoryItem(BaseModel):
    key: str
    value: str
    category: Optional[str] = "preference"

class VisualMemoryItem(BaseModel):
    object_name: str
    location_context: str
    room: str = "room"
    spatial_relationship: Optional[str] = None
    confidence: float = 0.9
    is_user_saved: bool = False
