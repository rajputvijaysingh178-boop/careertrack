"""OWNER: M1 - shared by every router
TODO(M1): implement get_current_user (decode JWT, load User) and require_admin.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "get_current_user not implemented yet")


def require_admin(user=Depends(get_current_user)):
    if getattr(user, "role", None) != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
