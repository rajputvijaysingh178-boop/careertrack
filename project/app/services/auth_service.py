"""OWNER: M1 (Job Board & Admin)
Responsibility: register, login, token creation
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
