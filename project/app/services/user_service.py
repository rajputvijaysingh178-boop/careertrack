"""OWNER: M1 (Job Board & Admin)
Responsibility: profile, admin user management
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class UserService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
