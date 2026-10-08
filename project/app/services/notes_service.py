"""OWNER: M2 (Application Tracker)
Responsibility: private notes per application
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class NotesService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
