"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.core.database import Base
from app.core.time import utcnow


class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    reminder_type = Column(String(50), nullable=False, default="FOLLOW_UP")
    reminder_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
