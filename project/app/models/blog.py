"""OWNER: M1 (Job Board & Admin)
Table: blogs
Columns to implement: id, title, slug, content, author_id, category, status, published_at, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M1): add remaining columns listed in the docstring
