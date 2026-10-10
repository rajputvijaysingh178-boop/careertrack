"""OWNER: M2 (Application Tracker)"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.core.database import Base
from app.core.time import utcnow


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    file_url = Column(String(1000), nullable=False)
    doc_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
