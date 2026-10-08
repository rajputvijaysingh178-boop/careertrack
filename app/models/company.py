"""OWNER: M1 (Job Board & Admin)
Table: companies
Columns to implement: id, name, logo_url, website, description, industry, location, company_size, created_at, status
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
