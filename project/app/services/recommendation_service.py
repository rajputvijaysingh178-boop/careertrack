"""OWNER: M3 (Interview Prep & Intelligence)
Responsibility: rule-based tag/skill matching for questions, materials, blogs, jobs
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
