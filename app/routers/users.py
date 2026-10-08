"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/ping")
def ping():
    return {"module": "users", "status": "ok"}
