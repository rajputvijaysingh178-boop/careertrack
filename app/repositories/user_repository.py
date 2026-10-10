"""OWNER: M1 - DB access for users (no business rules)"""
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == (email or "").strip().lower()).first()

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def search(self, q: Optional[str] = None, role: Optional[str] = None, status: Optional[str] = None,
               skip: int = 0, limit: int = 20) -> Tuple[List[User], int]:
        query = self.db.query(User)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)
        total = query.count()
        return query.order_by(User.id.desc()).offset(skip).limit(limit).all(), total

    def count(self, **filters) -> int:
        return self.db.query(User).filter_by(**filters).count()
