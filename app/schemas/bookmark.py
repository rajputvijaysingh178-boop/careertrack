"""OWNER: M2 (Application Tracker)"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BookmarkCreate(BaseModel):
    job_id: int
    type: str = "SAVE"


class BookmarkUpdate(BaseModel):
    type: str


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    job_id: int
    type: str
    created_at: datetime
