"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.core.database import Base
from app.core.time import utcnow


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    round_name = Column(String(100), nullable=False)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    mode = Column(String(30), nullable=True)
    interviewer = Column(String(255), nullable=True)
    meeting_link = Column(String(1000), nullable=True)
    status = Column(String(32), nullable=False, default="SCHEDULED", index=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class InterviewStatusHistory(Base):
    __tablename__ = "interview_status_history"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    round_name = Column(String(100), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    mode = Column(String(30), nullable=True)
    interviewer = Column(String(255), nullable=True)
    meeting_link = Column(String(1000), nullable=True)
    changed_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    feedback = Column(Text, nullable=True)
