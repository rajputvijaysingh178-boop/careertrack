"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.core.time import utcnow


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    event_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class HRCall(Base):
    __tablename__ = "hr_calls"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    hr_name = Column(String(200), nullable=True)
    company_name = Column(String(200), nullable=True)
    call_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    phone = Column(String(100), nullable=True)
    discussion = Column(Text, nullable=True)
    next_round = Column(String(200), nullable=True)
    interview_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
