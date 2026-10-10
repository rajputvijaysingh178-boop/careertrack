"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.application import Application
from app.models.interview import Interview, InterviewStatusHistory


class InterviewRepository:
    def __init__(self, db: Session):
        self.db = db
        self.base = BaseRepository(db, Interview)

    def application_owned(self, application_id: int, user_id: int):
        return self.db.query(Application).filter_by(id=application_id, user_id=user_id).first()

    def for_application(self, application_id: int):
        return self.db.query(Interview).filter_by(application_id=application_id).order_by(
            Interview.scheduled_at, Interview.id).all()

    def owned(self, interview_id: int, user_id: int):
        return self.db.query(Interview).join(Application).filter(
            Interview.id == interview_id, Application.user_id == user_id).first()

    def history(self, interview_id: int):
        return (self.db.query(InterviewStatusHistory).filter_by(interview_id=interview_id)
                .order_by(InterviewStatusHistory.changed_at, InterviewStatusHistory.id).all())
