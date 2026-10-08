"""OWNER: M2 (Application Tracker)
Responsibility: schedule rounds, HR call capture
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
