"""OWNER: M1 (Job Board & Admin)
Table: users
Columns to implement: id, name, email, password_hash, role(ADMIN/USER), phone, location, created_at, status
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
