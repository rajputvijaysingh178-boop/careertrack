"""OWNER: M1
Responsibility: register, login, token creation.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserOut, UserRegister


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def register(self, data: UserRegister) -> User:
        """Public sign-up always creates a normal USER. Admins are created by seed/admin only."""
        email = str(data.email).strip().lower()
        if self.users.get_by_email(email):
            raise DuplicateError("An account with this email already exists")
        return self.users.add(User(name=data.name.strip(), email=email, password_hash=hash_password(data.password),
                                   phone=data.phone, location=data.location, role="USER", status="ACTIVE"))

    def login(self, email: str, password: str) -> dict:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
        if user.status != "ACTIVE":
            raise HTTPException(403, "This account is blocked")
        return {"access_token": create_access_token(str(user.id), user.role), "token_type": "bearer",
                "user": UserOut.model_validate(user).model_dump(mode="json")}
