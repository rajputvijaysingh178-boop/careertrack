"""OWNER: M1 (Job Board & Admin)
Table: materials
Columns to implement: id, title, description, type, file_url, skill_id, job_id, company_id, created_by, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
