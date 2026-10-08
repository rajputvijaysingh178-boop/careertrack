"""OWNER: M2 (Application Tracker)
Responsibility: status counts, response/interview/offer rates, source analytics
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
