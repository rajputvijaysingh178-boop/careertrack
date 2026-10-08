"""OWNER: M1 (Job Board & Admin)
Responsibility: company CRUD
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
