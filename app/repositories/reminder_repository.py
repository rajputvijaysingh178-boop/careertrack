"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.application import Application
from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db
        self.base = BaseRepository(db, Reminder)

    def application_owned(self, application_id: int, user_id: int):
        return self.db.query(Application.id).filter_by(id=application_id, user_id=user_id).first()

    def for_user(self, user_id: int, status: str | None = None):
        query = self.db.query(Reminder).filter_by(user_id=user_id)
        if status:
            query = query.filter(Reminder.status == status.upper())
        return query.order_by(Reminder.reminder_time).all()

    def owned(self, reminder_id: int, user_id: int):
        return self.db.query(Reminder).filter_by(id=reminder_id, user_id=user_id).first()
