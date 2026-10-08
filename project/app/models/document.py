"""OWNER: M2 (Application Tracker)
Table: documents
Columns to implement: id, user_id, application_id, name, file_url, doc_type, created_at
"""
from sqlalchemy import Column, Integer
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    # TODO(M2): add remaining columns listed in the docstring
