"""OWNER: M1 - study material schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MATERIAL_TYPES = ("PDF", "VIDEO", "ARTICLE", "CHEATSHEET", "DOCUMENT", "LINK")


def _type(v):
    if v is None:
        return v
    v = str(v).strip().upper()
    if v not in MATERIAL_TYPES:
        raise ValueError(f"type must be one of {', '.join(MATERIAL_TYPES)}")
    return v


class MaterialCreate(BaseModel):
    title: str = Field(min_length=2, max_length=250)
    description: Optional[str] = None
    type: str = "LINK"
    file_url: str = Field(min_length=3, max_length=500)
    skill_id: Optional[int] = None
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    role: Optional[str] = Field(default=None, max_length=100)
    interview_round: Optional[str] = Field(default=None, max_length=50)

    _type = field_validator("type", mode="before")(_type)


class MaterialUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=250)
    description: Optional[str] = None
    type: Optional[str] = None
    file_url: Optional[str] = Field(default=None, min_length=3, max_length=500)
    skill_id: Optional[int] = None
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    role: Optional[str] = Field(default=None, max_length=100)
    interview_round: Optional[str] = Field(default=None, max_length=50)

    _type = field_validator("type", mode="before")(_type)


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str] = None
    type: str
    file_url: str
    skill_id: Optional[int] = None
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    role: Optional[str] = None
    interview_round: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


class MaterialPage(BaseModel):
    items: List[MaterialOut]
    total: int
    skip: int
    limit: int
