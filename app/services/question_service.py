"""OWNER: M3 (Interview Prep & Intelligence)
Responsibility: question bank CRUD + user question memory
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class QuestionService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
