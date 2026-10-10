"""OWNER: M3 - schemas for the user's personal interview memory bank"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.interview_question import _norm_difficulty


class UserQuestionBase(BaseModel):
    question: str = Field(min_length=5)
    application_id: Optional[int] = None
    category: Optional[str] = Field(default=None, max_length=100)
    asked_by: Optional[str] = Field(default=None, max_length=150)
    round: Optional[str] = Field(default=None, max_length=50)
    difficulty: Optional[str] = None
    my_answer: Optional[str] = None
    need_to_improve: Optional[str] = None

    _check_difficulty = field_validator("difficulty", mode="before")(_norm_difficulty)


class UserQuestionCreate(UserQuestionBase):
    pass


class UserQuestionUpdate(BaseModel):
    question: Optional[str] = Field(default=None, min_length=5)
    application_id: Optional[int] = None
    category: Optional[str] = Field(default=None, max_length=100)
    asked_by: Optional[str] = Field(default=None, max_length=150)
    round: Optional[str] = Field(default=None, max_length=50)
    difficulty: Optional[str] = None
    my_answer: Optional[str] = None
    need_to_improve: Optional[str] = None

    _check_difficulty = field_validator("difficulty", mode="before")(_norm_difficulty)


class UserQuestionOut(UserQuestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: Optional[datetime] = None


class UserQuestionPage(BaseModel):
    items: List[UserQuestionOut]
    total: int
    skip: int
    limit: int
