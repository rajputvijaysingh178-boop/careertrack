"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.application import Application, ApplicationStatusHistory


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db
        self.base = BaseRepository(db, Application)

    def owned(self, application_id: int, user_id: int):
        return self.db.query(Application).filter_by(id=application_id, user_id=user_id).first()

    def for_user(self, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100):
        query = self.db.query(Application).filter_by(user_id=user_id)
        if status:
            query = query.filter(Application.status == status.upper())
        return query.order_by(Application.updated_at.desc(), Application.id.desc()).offset(skip).limit(limit).all()

    def history(self, application_id: int):
        return (self.db.query(ApplicationStatusHistory).filter_by(application_id=application_id)
                .order_by(ApplicationStatusHistory.changed_at, ApplicationStatusHistory.id).all())
