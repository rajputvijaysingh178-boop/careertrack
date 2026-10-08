"""OWNER: M1 (Job Board & Admin)
Responsibility: material CRUD, link to job/skill/company
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class MaterialService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
