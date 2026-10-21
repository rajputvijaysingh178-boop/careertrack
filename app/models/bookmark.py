"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from app.core.database import Base
from app.core.time import utcnow


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True, index=True)
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_bookmark_user_job"),)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(16), nullable=False, default="SAVE")
    created_at = Column(DateTime, nullable=False, default=utcnow)
