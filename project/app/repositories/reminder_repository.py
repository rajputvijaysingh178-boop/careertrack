"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db
    # TODO: queries for reminder
