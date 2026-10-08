"""OWNER: M2 (Application Tracker)
Responsibility: Apply & Track, JD snapshot, state machine transitions, timeline
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
