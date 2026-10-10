"""OWNER: M3 - schemas for the admin question bank"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

DIFFICULTIES = ("EASY", "MEDIUM", "HARD")


def _norm_difficulty(v):
    if v is None:
        return v
    v = str(v).strip().upper()
    if v not in DIFFICULTIES:
        raise ValueError("difficulty must be EASY, MEDIUM or HARD")
    return v


class InterviewQuestionBase(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=5)
    difficulty: str = "MEDIUM"
    experience_level: Optional[str] = Field(default=None, max_length=30)
    round: Optional[str] = Field(default=None, max_length=50)
    expected_topics: Optional[List[str]] = None
    answer: Optional[str] = None
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    skill_id: Optional[int] = None

    _check_difficulty = field_validator("difficulty", mode="before")(_norm_difficulty)


class InterviewQuestionCreate(InterviewQuestionBase):
    pass


class InterviewQuestionUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    question: Optional[str] = Field(default=None, min_length=5)
    difficulty: Optional[str] = None
    experience_level: Optional[str] = Field(default=None, max_length=30)
    round: Optional[str] = Field(default=None, max_length=50)
    expected_topics: Optional[List[str]] = None
    answer: Optional[str] = None
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    skill_id: Optional[int] = None

    _check_difficulty = field_validator("difficulty", mode="before")(_norm_difficulty)


class InterviewQuestionOut(InterviewQuestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


class QuestionPage(BaseModel):
    items: List[InterviewQuestionOut]
    total: int
    skip: int
    limit: int
