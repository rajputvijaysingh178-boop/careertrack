"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.core.time import normalize_utc
from app.models.application import Application
from app.models.interview import Interview, InterviewStatusHistory
from app.repositories.interview_repository import InterviewRepository


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InterviewRepository(db)

    def list_for_application(self, application_id: int, user_id: int):
        self._application(application_id, user_id)
        return self.repo.for_application(application_id)

    def _application(self, application_id: int, user_id: int):
        app = self.repo.application_owned(application_id, user_id)
        if not app:
            raise NotFoundError("Application")
        return app

    def create(self, application_id: int, user_id: int, data):
        self._application(application_id, user_id)
        values = data.model_dump()
        values["scheduled_at"] = normalize_utc(values.get("scheduled_at"))
        item = Interview(application_id=application_id, **values)
        self.db.add(item)
        self.db.flush()
        self.db.add(self._history_snapshot(item, old_status=None))
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, interview_id: int, user_id: int, data):
        item = self.repo.owned(interview_id, user_id)
        if not item:
            raise NotFoundError("Interview")
        values = data.model_dump(exclude_unset=True)
        if "scheduled_at" in values:
            values["scheduled_at"] = normalize_utc(values["scheduled_at"])
        old_status = item.status
        old_values = {key: getattr(item, key) for key in values}
        for key, value in values.items():
            if value is None and not Interview.__table__.columns[key].nullable:
                continue
            setattr(item, key, value)
        if any(getattr(item, key) != old_values[key] for key in values):
            self.db.add(self._history_snapshot(item, old_status=old_status))
        self.db.commit()
        self.db.refresh(item)
        return item

    @staticmethod
    def _history_snapshot(item: Interview, old_status: str | None) -> InterviewStatusHistory:
        return InterviewStatusHistory(
            interview_id=item.id,
            old_status=old_status,
            new_status=item.status,
            round_name=item.round_name,
            scheduled_at=item.scheduled_at,
            mode=item.mode,
            interviewer=item.interviewer,
            meeting_link=item.meeting_link,
            feedback=item.feedback,
        )

    def history(self, interview_id: int, user_id: int):
        item = self.repo.owned(interview_id, user_id)
        if not item:
            raise NotFoundError("Interview")
        return self.repo.history(interview_id)

    def delete(self, interview_id: int, user_id: int):
        item = self.repo.owned(interview_id, user_id)
        if not item:
            raise NotFoundError("Interview")
        self.db.delete(item)
        self.db.commit()
        return None
