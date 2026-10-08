"""OWNER: M3 (Interview Prep & Intelligence)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db
    # TODO: queries for question
