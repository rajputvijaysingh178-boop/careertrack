"""OWNER: M3 - request bodies for JD analyzer, recommendations, prep plan"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class JDAnalyzeRequest(BaseModel):
    jd_text: str = Field(min_length=20, description="Paste the full job description")
    use_ai: bool = False


class PlanRequest(BaseModel):
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    jd_text: Optional[str] = None
    days: int = Field(default=7, ge=3, le=30)
    use_ai: bool = False


class PrepWorkspaceRequest(BaseModel):
    role_title: str = Field(min_length=1, max_length=200)
    jd_text: Optional[str] = None

    @field_validator("role_title")
    @classmethod
    def require_role_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("role_title cannot be blank")
        return value


class MySkillsUpdate(BaseModel):
    skills: List[str] = Field(description="Skill names, e.g. ['Python', 'FastAPI']")
