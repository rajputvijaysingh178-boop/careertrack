"""OWNER: M1 (Job Board & Admin)
Table: jobs
Columns to implement: id, company_id, title, description, location, employment_type, experience_min/max, salary_min/max, application_url, posted_date, expiry_date, status(DRAFT/PUBLISHED/ACTIVE/EXPIRED/CLOSED), created_by, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
