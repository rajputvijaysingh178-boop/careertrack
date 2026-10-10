"""OWNER: M2 (Application Tracker)"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InterviewCreate(BaseModel):
    round_name: str = Field(min_length=1, max_length=100)
    scheduled_at: Optional[datetime] = None
    mode: Optional[str] = Field(None, max_length=30)
    interviewer: Optional[str] = None
    meeting_link: Optional[str] = None
    status: str = "SCHEDULED"
    feedback: Optional[str] = None


class InterviewUpdate(BaseModel):
    round_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    scheduled_at: Optional[datetime] = None
    mode: Optional[str] = Field(default=None, max_length=30)
    interviewer: Optional[str] = None
    meeting_link: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    round_name: str
    scheduled_at: Optional[datetime]
    mode: Optional[str]
    interviewer: Optional[str]
    meeting_link: Optional[str]
    status: str
    feedback: Optional[str]
    created_at: datetime
    updated_at: datetime
