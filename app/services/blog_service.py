"""OWNER: M1 (Job Board & Admin)
Responsibility: blog CRUD, slug, publish
Business rules live here (not in routers or repositories)."""
from sqlalchemy.orm import Session


class BlogService:
    def __init__(self, db: Session):
        self.db = db
    # TODO: implement
