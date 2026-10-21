"""OWNER: M2 (Application Tracker)"""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.application import Application, ApplicationStatusHistory
from app.models.application_event import ApplicationEvent, HRCall
from app.models.company import Company
from app.models.job import Job
from app.models.skill import JobSkill, Skill
from app.repositories.application_repository import ApplicationRepository
from app.core.time import normalize_utc, utcnow
from app.workflows.application_state_machine import validate_transition


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ApplicationRepository(db)

    def _owned(self, application_id: int, user_id: int) -> Application:
        item = self.repo.owned(application_id, user_id)
        if not item:
            raise NotFoundError("Application")
        return item

    def list(self, user_id: int, status: str | None = None, skip: int = 0, limit: int = 100):
        return self.repo.for_user(user_id, status, skip, limit)

    def get(self, application_id: int, user_id: int):
        return self._owned(application_id, user_id)

    def create(self, user_id: int, data):
        values = data.model_dump(exclude_unset=True)
        job = self.db.get(Job, values.get("job_id")) if values.get("job_id") else None
        if values.get("job_id") and not job:
            raise NotFoundError("Job")
        company = self.db.get(Company, values.get("company_id")) if values.get("company_id") else None
        if values.get("company_id") and not company:
            raise NotFoundError("Company")
        if job:
            company = self.db.get(Company, job.company_id)
            values["company_id"] = job.company_id
            values["job_title"] = job.title
            values["company_name"] = company.name if company else None
            values["jd_text"] = job.description
            values["salary"] = f"{job.salary_min or ''}-{job.salary_max or ''}".strip("-")
            values["location"] = job.location
            values["application_url"] = job.application_url
            skills = (self.db.query(Skill.name).join(JobSkill, JobSkill.skill_id == Skill.id)
                      .filter(JobSkill.job_id == job.id).all())
            values["skills"] = ", ".join(s[0] for s in skills)
        elif company:
            values.setdefault("company_name", company.name)
        if not values.get("job_title"):
            raise ValueError("job_title is required when creating an application without a job_id")
        initial = str(values.get("status") or "SAVED").upper()
        if initial not in ("SAVED", "APPLIED"):
            raise ValueError("New applications must start in SAVED or APPLIED status")
        values.update(user_id=user_id, status=initial)
        values["applied_date"] = normalize_utc(values.get("applied_date"))
        if initial == "APPLIED" and not values.get("applied_date"):
            values["applied_date"] = utcnow()
        item = Application(**values)
        self.db.add(item)
        self.db.flush()
        self.db.add(ApplicationStatusHistory(application_id=item.id, old_status=None, new_status=initial,
                                             changed_by=user_id, comment="Application created"))
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, application_id: int, user_id: int, data):
        item = self._owned(application_id, user_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is None and not Application.__table__.columns[key].nullable:
                continue
            if key == "applied_date":
                value = normalize_utc(value)
            setattr(item, key, value)
        item.updated_at = utcnow()
        self.db.commit()
        self.db.refresh(item)
        return item

    def change_status(self, application_id: int, user_id: int, status: str, comment: str | None = None):
        item = self._owned(application_id, user_id)
        new = status.strip().upper()
        validate_transition(item.status, new)
        old = item.status
        item.status = new
        item.updated_at = utcnow()
        if new == "APPLIED" and not item.applied_date:
            item.applied_date = utcnow()
        self.db.add(ApplicationStatusHistory(application_id=item.id, old_status=old, new_status=new,
                                             comment=comment, changed_by=user_id))
        self.db.commit()
        self.db.refresh(item)
        return item

    def history(self, application_id: int, user_id: int):
        self._owned(application_id, user_id)
        return self.repo.history(application_id)

    def add_event(self, application_id: int, user_id: int, data):
        self._owned(application_id, user_id)
        values = data.model_dump()
        values["event_at"] = normalize_utc(values.get("event_at")) or utcnow()
        item = ApplicationEvent(application_id=application_id, **values)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def events(self, application_id: int, user_id: int):
        self._owned(application_id, user_id)
        return (self.db.query(ApplicationEvent).filter_by(application_id=application_id)
                .order_by(ApplicationEvent.event_at, ApplicationEvent.id).all())

    def add_hr_call(self, application_id: int, user_id: int, data):
        app = self._owned(application_id, user_id)
        values = data.model_dump()
        values["call_at"] = normalize_utc(values.get("call_at")) or utcnow()
        values["interview_at"] = normalize_utc(values.get("interview_at"))
        if not values.get("company_name"):
            values["company_name"] = app.company_name
        item = HRCall(application_id=application_id, **values)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def hr_calls(self, application_id: int, user_id: int):
        self._owned(application_id, user_id)
        return (self.db.query(HRCall).filter_by(application_id=application_id)
                .order_by(HRCall.call_at.desc(), HRCall.id.desc()).all())
