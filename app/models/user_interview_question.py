"""OWNER: M3 (Interview Prep & Intelligence)
Table: user_interview_questions  (a user's PRIVATE interview memory bank)
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


class UserInterviewQuestion(Base):
    __tablename__ = "user_interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True, index=True)

    question = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)      # optional, used by interview analytics
    asked_by = Column(String(150), nullable=True)      # company name, e.g. Deloitte
    round = Column(String(50), nullable=True)          # Technical Round 1 ...
    difficulty = Column(String(20), nullable=True)
    my_answer = Column(Text, nullable=True)
    need_to_improve = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
