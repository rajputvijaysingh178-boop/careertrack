"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("/ping")
def ping():
    return {"module": "interviews", "status": "ok"}
