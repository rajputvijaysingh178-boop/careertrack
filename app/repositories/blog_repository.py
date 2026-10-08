"""OWNER: M1 (Job Board & Admin)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository


class BlogRepository:
    def __init__(self, db: Session):
        self.db = db
    # TODO: queries for blog
