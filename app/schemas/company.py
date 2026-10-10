"""OWNER: M1 - company schemas"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = None
    industry: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=150)
    company_size: Optional[str] = Field(default=None, max_length=50)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website: Optional[str] = Field(default=None, max_length=300)
    description: Optional[str] = None
    industry: Optional[str] = Field(default=None, max_length=100)
    location: Optional[str] = Field(default=None, max_length=150)
    company_size: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v):
        if v is None:
            return v
        v = str(v).strip().upper()
        if v not in ("ACTIVE", "INACTIVE"):
            raise ValueError("status must be ACTIVE or INACTIVE")
        return v


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: Optional[datetime] = None
    active_jobs: Optional[int] = None


class CompanyPage(BaseModel):
    items: List[CompanyOut]
    total: int
    skip: int
    limit: int
