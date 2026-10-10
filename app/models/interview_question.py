"""OWNER: M3 (Interview Prep & Intelligence)
Table: interview_questions  (admin-managed question bank)
"""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)

    # Targeting: all optional, so one question can be generic or company/job/skill specific
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True, index=True)

    category = Column(String(100), nullable=False, index=True)         # Python, SQL, System Design ...
    question = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False, default="MEDIUM")  # EASY / MEDIUM / HARD
    experience_level = Column(String(30), nullable=True)               # "1-3 Years"
    round = Column(String(50), nullable=True)                          # Technical 1, HR ...
    expected_topics = Column(JSON, nullable=True)                      # ["Functions", "Closures"]
    answer = Column(Text, nullable=True)                               # model answer

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)