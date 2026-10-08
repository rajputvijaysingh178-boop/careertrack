"""OWNER: M2 (Application Tracker)
Responsibility: create/list/due reminders
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class ReminderService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
