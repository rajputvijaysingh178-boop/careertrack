"""OWNER: M1 - blog schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _status(v):
    if v is None:
        return v
    v = str(v).strip().upper()
    if v not in ("DRAFT", "PUBLISHED"):
        raise ValueError("status must be DRAFT or PUBLISHED")
    return v


class BlogCreate(BaseModel):
    title: str = Field(min_length=3, max_length=250)
    content: str = Field(min_length=10)
    category: Optional[str] = Field(default=None, max_length=100)
    tags: List[str] = []
    status: str = "DRAFT"
    slug: Optional[str] = Field(default=None, max_length=250)     # auto-generated from the title if empty

    _status = field_validator("status", mode="before")(_status)


class BlogUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=250)
    content: Optional[str] = Field(default=None, min_length=10)
    category: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = None
    status: Optional[str] = None

    _status = field_validator("status", mode="before")(_status)


class BlogSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    slug: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: str
    author_id: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class BlogOut(BlogSummary):
    content: str


class BlogPage(BaseModel):
    items: List[BlogSummary]
    total: int
    skip: int
    limit: int
