"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("/ping")
def ping():
    return {"module": "blogs", "status": "ok"}
