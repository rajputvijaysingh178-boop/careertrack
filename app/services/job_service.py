"""OWNER: M1 (Job Board & Admin)
Responsibility: CRUD, publish, expire, duplicate detection, search/filter
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class JobService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
