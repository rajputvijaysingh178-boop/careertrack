"""OWNER: M1 (Job Board & Admin)
Table: blogs   Status: DRAFT / PUBLISHED
"""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)                       # ["Python", "Interview"]
    status = Column(String(10), nullable=False, default="DRAFT", index=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
