"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.application import Application
from app.models.note import Note


class NoteRepository:
    def __init__(self, db: Session):
        self.db = db
        self.base = BaseRepository(db, Note)

    def application_owned(self, application_id: int, user_id: int):
        return self.db.query(Application.id).filter_by(id=application_id, user_id=user_id).first()

    def for_user(self, user_id: int, application_id: int | None = None):
        query = self.db.query(Note).filter_by(user_id=user_id)
        if application_id is not None:
            query = query.filter_by(application_id=application_id)
        return query.order_by(Note.updated_at.desc()).all()

    def owned(self, note_id: int, user_id: int):
        return self.db.query(Note).filter_by(id=note_id, user_id=user_id).first()
