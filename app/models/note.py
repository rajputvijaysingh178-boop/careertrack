"""OWNER: M2 (Application Tracker)
Table: notes
Columns to implement: id, user_id, application_id, title, content, created_at, updated_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
