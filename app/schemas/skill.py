"""OWNER: M1 - skill schemas"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category: Optional[str] = None


class SkillBulk(BaseModel):
    skills: List[SkillCreate]
