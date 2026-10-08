"""OWNER: M1 (Job Board & Admin)
Table: skills
Columns to implement: id, name, category  (+ job_skills: job_id, skill_id, importance REQUIRED/PREFERRED/OPTIONAL)
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
