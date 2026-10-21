"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.core.time import normalize_utc
from app.models.application import Application
from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository


class ReminderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReminderRepository(db)

    def list(self, user_id: int, status: str | None = None):
        return self.repo.for_user(user_id, status)

    def create(self, user_id: int, data):
        if data.application_id is not None and not self.repo.application_owned(data.application_id, user_id):
            raise NotFoundError("Application")
        values = data.model_dump()
        values["reminder_time"] = normalize_utc(values["reminder_time"])
        item = Reminder(user_id=user_id, **values)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, reminder_id: int, user_id: int, data):
        item = self.repo.owned(reminder_id, user_id)
        if not item:
            raise NotFoundError("Reminder")
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is None and not Reminder.__table__.columns[key].nullable:
                continue
            if key == "reminder_time":
                value = normalize_utc(value)
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, reminder_id: int, user_id: int):
        item = self.repo.owned(reminder_id, user_id)
        if not item:
            raise NotFoundError("Reminder")
        self.db.delete(item)
        self.db.commit()
