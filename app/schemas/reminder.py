"""OWNER: M2 (Application Tracker)
Pydantic request/response schemas for reminders."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    application_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=255)
    reminder_type: str = "FOLLOW_UP"
    reminder_time: datetime


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    reminder_type: Optional[str] = None
    reminder_time: Optional[datetime] = None
    status: Optional[str] = None


class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    application_id: Optional[int]
    title: str
    reminder_type: str
    reminder_time: datetime
    status: str
    created_at: datetime
