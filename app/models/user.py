"""OWNER: M1 (Job Board & Admin)
Table: users   Roles: ADMIN / USER   Status: ACTIVE / BLOCKED
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)   # stored lowercase
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="USER", index=True)
    phone = Column(String(30), nullable=True)
    location = Column(String(150), nullable=True)
    status = Column(String(10), nullable=False, default="ACTIVE", index=True)
    created_at = Column(DateTime, default=datetime.now)
