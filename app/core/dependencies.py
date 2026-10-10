"""OWNER: M1 - shared by EVERY router (M2 and M3 import get_current_user / require_admin from here)."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_UNAUTHORIZED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
                              headers={"WWW-Authenticate": "Bearer"})


def is_admin(user) -> bool:
    return user is not None and str(getattr(user, "role", "")).upper().endswith("ADMIN")


def _user_from_token(token: str, db: Session):
    try:
        user_id = int(decode_token(token)["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        raise _UNAUTHORIZED
    user = UserRepository(db).get(user_id)
    if not user:
        raise _UNAUTHORIZED
    if user.status != "ACTIVE":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is blocked")
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return _user_from_token(token, db)


def get_optional_user(token: Optional[str] = Depends(oauth2_optional), db: Session = Depends(get_db)):
    """For public endpoints that behave differently for admins. Returns None for anonymous visitors."""
    if not token:
        return None
    return _user_from_token(token, db)


def require_admin(user=Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
