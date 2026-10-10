"""OWNER: M2 (Application Tracker)
Pydantic request/response schemas for notes."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    application_id: int
    title: str = Field(min_length=1, max_length=255)
    content: str = ""


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    application_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
