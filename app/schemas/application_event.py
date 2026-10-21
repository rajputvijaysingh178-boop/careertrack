"""OWNER: M2 (Application Tracker)"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    details: str | None = None
    event_at: datetime | None = None


class ApplicationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    title: str
    details: str | None
    event_at: datetime
    created_at: datetime


class HRCallCreate(BaseModel):
    hr_name: str | None = Field(default=None, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    call_at: datetime | None = None
    phone: str | None = Field(default=None, max_length=100)
    discussion: str | None = None
    next_round: str | None = Field(default=None, max_length=200)
    interview_at: datetime | None = None
    notes: str | None = None


class HRCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    hr_name: str | None
    company_name: str | None
    call_at: datetime
    phone: str | None
    discussion: str | None
    next_round: str | None
    interview_at: datetime | None
    notes: str | None
    created_at: datetime
