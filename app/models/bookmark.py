"""OWNER: M2 (Application Tracker)
Table: bookmarks
Columns to implement: id, user_id, job_id, type(SAVE/APPLY/IGNORE), created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
