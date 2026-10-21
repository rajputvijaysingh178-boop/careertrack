"""OWNER: M1 (Job Board & Admin)
Tables: materials, material_bookmarks
Types: PDF / VIDEO / ARTICLE / CHEATSHEET / DOCUMENT / LINK
A material can be attached to a job, role, skill, interview round and/or company.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(15), nullable=False, default="LINK", index=True)
    file_url = Column(String(500), nullable=False)                 # external URL or uploads/materials/<file>
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    role = Column(String(100), nullable=True)                      # e.g. QA Automation Engineer
    interview_round = Column(String(50), nullable=True)            # e.g. Technical 1
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class MaterialBookmark(Base):
    __tablename__ = "material_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "material_id", name="uq_material_bookmark"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
