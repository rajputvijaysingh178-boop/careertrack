"""OWNER: M3 (Interview Prep & Intelligence)
Table: user_interview_questions
Columns to implement: id, user_id, application_id, question, asked_by, round, difficulty, my_answer, need_to_improve, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class UserInterviewQuestion(Base):
    __tablename__ = "user_interview_questions"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M3): add remaining columns listed in the docstring
