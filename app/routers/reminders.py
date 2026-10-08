"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/ping")
def ping():
    return {"module": "reminders", "status": "ok"}
