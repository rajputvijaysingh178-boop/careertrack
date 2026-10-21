"""OWNER: M1 - job schemas"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

WORK_MODES = ("REMOTE", "HYBRID", "ONSITE")
EMPLOYMENT_TYPES = ("FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "FREELANCE")
IMPORTANCE = ("REQUIRED", "PREFERRED", "OPTIONAL")


def _enum(allowed, label):
    def check(v):
        if v is None:
            return v
        v = str(v).strip().upper().replace("-", "_").replace(" ", "_")
        if v == "ON_SITE":
            v = "ONSITE"
        if v not in allowed:
            raise ValueError(f"{label} must be one of {', '.join(allowed)}")
        return v
    return check


class JobSkillIn(BaseModel):
    """Give skill_id OR name (an unknown name is added to the skills table automatically)."""
    skill_id: Optional[int] = None
    name: Optional[str] = Field(default=None, max_length=100)
    importance: str = "REQUIRED"

    _imp = field_validator("importance", mode="before")(_enum(IMPORTANCE, "importance"))

    @model_validator(mode="after")
    def _one_of(self):
        if self.skill_id is None and not (self.name and self.name.strip()):
            raise ValueError("provide skill_id or name")
        return self


class _JobFields(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=20)
    location: Optional[str] = Field(default=None, max_length=150)
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    job_type: Optional[str] = Field(default=None, max_length=50)
    experience_min: Optional[int] = Field(default=None, ge=0, le=60)
    experience_max: Optional[int] = Field(default=None, ge=0, le=60)
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    application_url: Optional[str] = Field(default=None, max_length=500)
    posted_date: Optional[date] = None
    expiry_date: Optional[date] = None

    _wm = field_validator("work_mode", mode="before")(_enum(WORK_MODES, "work_mode"))
    _et = field_validator("employment_type", mode="before")(_enum(EMPLOYMENT_TYPES, "employment_type"))

    @model_validator(mode="after")
    def _ranges(self):
        if self.experience_min is not None and self.experience_max is not None \
                and self.experience_min > self.experience_max:
            raise ValueError("experience_min cannot be greater than experience_max")
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max")
        return self


class JobCreate(_JobFields):
    company_id: int
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    skills: List[JobSkillIn] = []


class JobUpdate(_JobFields):
    company_id: Optional[int] = None
    skills: Optional[List[JobSkillIn]] = None     # when given, REPLACES the job's skills


class JobSkillsReplace(BaseModel):
    skills: List[JobSkillIn]


class ReopenBody(BaseModel):
    expiry_date: Optional[date] = None


class DuplicateCheck(BaseModel):
    company_id: int
    title: str
    description: Optional[str] = ""
    exclude_job_id: Optional[int] = None


class CompanyBrief(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None


class JobSkillOut(BaseModel):
    id: int
    name: str
    importance: str


class JobOut(BaseModel):
    id: int
    company: Optional[CompanyBrief] = None
    title: str
    description: Optional[str] = None            # omitted in list responses
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    job_type: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    application_url: Optional[str] = None
    posted_date: Optional[date] = None
    posted_days_ago: Optional[int] = None
    expiry_date: Optional[date] = None
    is_expired: bool = False
    status: str
    skills: List[JobSkillOut] = []
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


class JobPage(BaseModel):
    items: List[JobOut]
    total: int
    skip: int
    limit: int
