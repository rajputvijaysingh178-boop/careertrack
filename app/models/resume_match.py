"""OWNER: M3 (Interview Prep & Intelligence)
Table: resume_matches  (history of Resume vs JD match results)
"""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class ResumeMatch(Base):
    __tablename__ = "resume_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    resume_filename = Column(String(255), nullable=True)
    match_percent = Column(Integer, nullable=False, default=0)
    matched = Column(JSON, nullable=True)
    missing = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
