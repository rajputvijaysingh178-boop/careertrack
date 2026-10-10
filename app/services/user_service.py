"""OWNER: M1
Responsibility: own profile, password change, admin user management.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import AdminUserCreate, PasswordChange, UserUpdateMe


class UserService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    # ---------------------------------------------------------------- self-service
    def update_me(self, user: User, data: UserUpdateMe) -> User:
        for key, value in data.model_dump(exclude_unset=True).items():
            if key == "name" and not value:
                continue
            setattr(user, key, value)
        self.users.commit()
        self.users.refresh(user)
        return user

    def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(400, "Current password is incorrect")
        user.password_hash = hash_password(data.new_password)
        self.users.commit()

    # ---------------------------------------------------------------- admin
    def get(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User")
        return user

    def admin_list(self, q: Optional[str], role: Optional[str], status: Optional[str], skip: int, limit: int):
        return self.users.search(q, role.upper() if role else None, status.upper() if status else None, skip, limit)

    def admin_create(self, data: AdminUserCreate) -> User:
        email = str(data.email).strip().lower()
        if self.users.get_by_email(email):
            raise DuplicateError("An account with this email already exists")
        return self.users.add(User(name=data.name.strip(), email=email, password_hash=hash_password(data.password),
                                   phone=data.phone, location=data.location, role=data.role, status="ACTIVE"))

    def set_status(self, admin: User, user_id: int, status: str) -> User:
        user = self.get(user_id)
        if user.id == admin.id:
            raise HTTPException(400, "You cannot block your own account")
        user.status = status
        self.users.commit()
        self.users.refresh(user)
        return user

    def set_role(self, admin: User, user_id: int, role: str) -> User:
        user = self.get(user_id)
        if user.id == admin.id:
            raise HTTPException(400, "You cannot change your own role")
        user.role = role
        self.users.commit()
        self.users.refresh(user)
        return user
