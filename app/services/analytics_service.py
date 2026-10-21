"""OWNER: M2 (Application Tracker)"""
from collections import Counter
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStatusHistory
from app.models.interview import Interview
from app.core.time import normalize_utc, utcnow


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def summary(self, user_id: int) -> dict:
        applications = self.db.query(Application).filter_by(user_id=user_id).all()
        ids = [a.id for a in applications]
        interviews = self.db.query(Interview).filter(Interview.application_id.in_(ids)).count() if ids else 0
        statuses = Counter(a.status for a in applications)
        sources = Counter((a.source or "Unknown") for a in applications)
        total = len(applications)
        history = self.db.query(ApplicationStatusHistory).filter(
            ApplicationStatusHistory.application_id.in_(ids)).all() if ids else []
        responded_ids = {h.application_id for h in history if h.new_status in {
            "APPLICATION_VIEWED", "SHORTLISTED", "HR_CONTACTED", "INTERVIEW_SCHEDULED",
            "INTERVIEW_1", "INTERVIEW_2", "HR_ROUND", "OFFER_RECEIVED", "ACCEPTED"}}
        interviewed_ids = {h.application_id for h in history if h.new_status in {
            "INTERVIEW_SCHEDULED", "INTERVIEW_1", "INTERVIEW_2", "HR_ROUND", "OFFER_RECEIVED", "ACCEPTED"}}
        offer_ids = {h.application_id for h in history if h.new_status in {"OFFER_RECEIVED", "ACCEPTED"}}
        source_ids = {}
        for app in applications:
            source_ids.setdefault(app.source or "Unknown", set()).add(app.id)
        by_source_response_rate = {
            source: round(len(app_ids & responded_ids) * 100 / len(app_ids), 1)
            for source, app_ids in source_ids.items()
        }
        upcoming = (self.db.query(Interview, Application).join(
            Application, Interview.application_id == Application.id
        ).filter(Application.user_id == user_id).all())
        upcoming_interviews = [{"interview_id": interview.id, "application_id": app.id,
                                "job_title": app.job_title, "company_name": app.company_name,
                                "round_name": interview.round_name, "scheduled_at": interview.scheduled_at,
                                "status": interview.status}
                               for interview, app in upcoming
                               if interview.scheduled_at and normalize_utc(interview.scheduled_at) >= utcnow()
                               and interview.status not in {"CANCELLED", "COMPLETED"}]
        upcoming_interviews.sort(key=lambda event: normalize_utc(event["scheduled_at"]))
        return {"total_applications": total, "by_status": dict(statuses), "by_source": dict(sources),
                "interview_rounds": interviews,
                "response_rate": round(len(responded_ids) * 100 / total, 1) if total else 0.0,
                "interview_rate": round(len(interviewed_ids) * 100 / total, 1) if total else 0.0,
                "offer_rate": round(len(offer_ids) * 100 / total, 1) if total else 0.0,
                "response_to_interview_rate": round(len(interviewed_ids) * 100 / len(responded_ids), 1)
                if responded_ids else 0.0,
                "interview_to_offer_rate": round(len(offer_ids) * 100 / len(interviewed_ids), 1)
                if interviewed_ids else 0.0,
                "by_source_response_rate": by_source_response_rate,
                "upcoming_interviews": upcoming_interviews}
