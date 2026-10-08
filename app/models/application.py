"""OWNER: M2 (Application Tracker)
Table: applications
Columns to implement: id, user_id, job_id, company_id, applied_date, status, source, application_url, resume_version, salary_expectation, hr_name, hr_contact, notes, JD SNAPSHOT fields (job_title, company_name, jd_text, skills, requirements, salary, location), created_at, updated_at  (+ application_status_history: id, application_id, old_status, new_status, changed_at, comment, changed_by)
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
