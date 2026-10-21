"""OWNER: M1 (Job Board & Admin)
Tables: skills, job_skills (many-to-many with importance REQUIRED / PREFERRED / OPTIONAL)
"""
from sqlalchemy import Column, ForeignKey, Integer, String

from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True, index=True)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    importance = Column(String(10), nullable=False, default="REQUIRED")
