"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/ping")
def ping():
    return {"module": "skills", "status": "ok"}
