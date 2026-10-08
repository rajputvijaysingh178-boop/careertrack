"""OWNER: M2 (Application Tracker)
Table: interviews
Columns to implement: id, application_id, round_name, scheduled_at, mode, interviewer, meeting_link, status, feedback, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
