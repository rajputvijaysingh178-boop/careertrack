"""OWNER: M1 (Job Board & Admin)
Table: jobs

Column names are a CONTRACT with M2 (JD snapshot reads them) and M3 (recommendations read them):
id, company_id, title, description, location, employment_type, experience_min, experience_max,
salary_min, salary_max, application_url, posted_date, expiry_date, status.
Salary values are in LPA (lakhs per annum), experience in years.
Status: DRAFT / PUBLISHED / ACTIVE / EXPIRED / CLOSED
"""
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(150), nullable=True, index=True)
    work_mode = Column(String(10), nullable=True, index=True)          # REMOTE / HYBRID / ONSITE
    employment_type = Column(String(20), nullable=True, index=True)    # FULL_TIME / PART_TIME / CONTRACT / INTERNSHIP / FREELANCE
    job_type = Column(String(50), nullable=True, index=True)           # role family: Backend, QA, DevOps, Data Science ...
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    application_url = Column(String(500), nullable=True)
    posted_date = Column(Date, nullable=True, index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    status = Column(String(10), nullable=False, default="DRAFT", index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
