"""OWNER: M2 (Application Tracker)"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApplicationCreate(BaseModel):
    job_id: Optional[int] = None
    company_id: Optional[int] = None
    job_title: Optional[str] = Field(default=None, max_length=200)
    company_name: Optional[str] = Field(default=None, max_length=200)
    jd_text: Optional[str] = None
    skills: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    applied_date: Optional[datetime] = None
    status: str = "SAVED"
    source: Optional[str] = None
    application_url: Optional[str] = None
    resume_version: Optional[str] = None
    salary_expectation: Optional[float] = None
    hr_name: Optional[str] = None
    hr_contact: Optional[str] = None

    @model_validator(mode="after")
    def valid_application_target(self):
        if not self.job_id and not (self.job_title and self.job_title.strip()):
            raise ValueError("Provide job_id or job_title")
        if self.status.upper() not in {"SAVED", "APPLIED"}:
            raise ValueError("New applications must start in SAVED or APPLIED status")
        return self


class ApplicationUpdate(BaseModel):
    job_title: Optional[str] = Field(default=None, max_length=200)
    company_name: Optional[str] = Field(default=None, max_length=200)
    jd_text: Optional[str] = None
    skills: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    applied_date: Optional[datetime] = None
    source: Optional[str] = None
    application_url: Optional[str] = None
    resume_version: Optional[str] = None
    salary_expectation: Optional[float] = None
    hr_name: Optional[str] = None
    hr_contact: Optional[str] = None


class StatusChange(BaseModel):
    status: str
    comment: Optional[str] = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    job_id: Optional[int]
    company_id: Optional[int]
    job_title: str
    company_name: Optional[str]
    jd_text: Optional[str]
    skills: Optional[str]
    requirements: Optional[str]
    salary: Optional[str]
    location: Optional[str]
    applied_date: Optional[datetime]
    status: str
    source: Optional[str]
    application_url: Optional[str]
    resume_version: Optional[str]
    salary_expectation: Optional[float]
    hr_name: Optional[str]
    hr_contact: Optional[str]
    created_at: datetime
    updated_at: datetime


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    old_status: Optional[str]
    new_status: str
    changed_at: datetime
    comment: Optional[str]
    changed_by: Optional[int]
