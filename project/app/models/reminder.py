"""OWNER: M2 (Application Tracker)
Table: reminders
Columns to implement: id, user_id, application_id, title, reminder_type, reminder_time, status, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
