"""OWNER: M1 - user / auth schemas"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    phone: Optional[str] = Field(default=None, max_length=30)
    location: Optional[str] = Field(default=None, max_length=150)


class UserLoginJSON(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    location: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdateMe(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    location: Optional[str] = Field(default=None, max_length=150)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class AdminUserCreate(UserRegister):
    role: str = "USER"

    @field_validator("role", mode="before")
    @classmethod
    def _role(cls, v):
        v = str(v).strip().upper()
        if v not in ("ADMIN", "USER"):
            raise ValueError("role must be ADMIN or USER")
        return v


class RoleChange(BaseModel):
    role: str

    @field_validator("role", mode="before")
    @classmethod
    def _role(cls, v):
        v = str(v).strip().upper()
        if v not in ("ADMIN", "USER"):
            raise ValueError("role must be ADMIN or USER")
        return v


class StatusChangeUser(BaseModel):
    status: str

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v):
        v = str(v).strip().upper()
        if v not in ("ACTIVE", "BLOCKED"):
            raise ValueError("status must be ACTIVE or BLOCKED")
        return v
