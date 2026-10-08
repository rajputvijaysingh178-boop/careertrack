"""OWNER: M3 (Interview Prep & Intelligence)
Table: interview_questions
Columns to implement: id, company_id, job_id, skill_id, category, question, difficulty, experience_level, round, expected_topics, answer, created_by, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M3): add remaining columns listed in the docstring
