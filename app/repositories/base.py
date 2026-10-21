"""OWNER: ALL - generic CRUD helper. Repositories contain DB access ONLY, no business rules."""
from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def get(self, id: int):
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 50):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()
