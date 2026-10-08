"""OWNER: M3 (Interview Prep & Intelligence)
Responsibility: extract skills/topics from JD (rule-based, then LLM)
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class JdAnalyzerService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
