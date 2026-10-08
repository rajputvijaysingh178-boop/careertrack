"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/ping")
def ping():
    return {"module": "materials", "status": "ok"}
