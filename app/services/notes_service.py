"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.note import Note
from app.repositories.note_repository import NoteRepository


class NotesService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NoteRepository(db)

    def _owned(self, application_id: int, user_id: int):
        if not self.repo.application_owned(application_id, user_id):
            raise NotFoundError("Application")

    def list(self, user_id: int, application_id: int | None = None):
        if application_id:
            self._owned(application_id, user_id)
        return self.repo.for_user(user_id, application_id)

    def create(self, user_id: int, data):
        self._owned(data.application_id, user_id)
        item = Note(user_id=user_id, **data.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, note_id: int, user_id: int, data):
        item = self.repo.owned(note_id, user_id)
        if not item:
            raise NotFoundError("Note")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, note_id: int, user_id: int):
        item = self.repo.owned(note_id, user_id)
        if not item:
            raise NotFoundError("Note")
        self.db.delete(item)
        self.db.commit()
