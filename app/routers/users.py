"""OWNER: M1 - my profile (admin user management is under /admin/users)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import PasswordChange, UserOut, UserUpdateMe
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/ping")
def ping():
    return {"module": "users", "status": "ok"}


@router.get("/me", response_model=UserOut)
def get_me(user=Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(data: UserUpdateMe, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return UserService(db).update_me(user, data)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChange, db: Session = Depends(get_db), user=Depends(get_current_user)):
    UserService(db).change_password(user, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
