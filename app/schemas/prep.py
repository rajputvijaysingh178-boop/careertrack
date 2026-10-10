"""OWNER: M3 - request bodies for JD analyzer, recommendations, prep plan"""
from typing import List, Optional

from pydantic import BaseModel, Field


class JDAnalyzeRequest(BaseModel):
    jd_text: str = Field(min_length=20, description="Paste the full job description")
    use_ai: bool = False


class PlanRequest(BaseModel):
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    jd_text: Optional[str] = None
    days: int = Field(default=7, ge=3, le=30)
    use_ai: bool = False


class MySkillsUpdate(BaseModel):
    skills: List[str] = Field(description="Skill names, e.g. ['Python', 'FastAPI']")
