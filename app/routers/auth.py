"""OWNER: M1 - authentication"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import TokenOut, UserLoginJSON, UserOut, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/ping")
def ping():
    return {"module": "auth", "status": "ok"}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Public sign-up (always creates a normal USER)."""
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Form login used by the Swagger 'Authorize' button. `username` = the email."""
    return AuthService(db).login(form.username, form.password)


@router.post("/login/json", response_model=TokenOut)
def login_json(data: UserLoginJSON, db: Session = Depends(get_db)):
    """Same as /auth/login but with a JSON body (easier for a frontend)."""
    return AuthService(db).login(str(data.email), data.password)


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user
