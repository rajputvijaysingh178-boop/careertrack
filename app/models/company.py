"""OWNER: M1 (Job Board & Admin)
Table: companies   Status: ACTIVE / INACTIVE
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True, index=True)
    location = Column(String(150), nullable=True)
    company_size = Column(String(50), nullable=True)
    status = Column(String(10), nullable=False, default="ACTIVE", index=True)
    created_at = Column(DateTime, default=datetime.now)
