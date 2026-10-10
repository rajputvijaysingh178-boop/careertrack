"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from app.core.database import Base
from app.core.time import utcnow


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    applied_date = Column(DateTime, nullable=True, index=True)
    status = Column(String(32), nullable=False, default="SAVED", index=True)
    source = Column(String(100), nullable=True)
    application_url = Column(String(1000), nullable=True)
    resume_version = Column(String(255), nullable=True)
    salary_expectation = Column(Float, nullable=True)
    hr_name = Column(String(200), nullable=True)
    hr_contact = Column(String(255), nullable=True)
    job_title = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=True)
    jd_text = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    salary = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    comment = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
