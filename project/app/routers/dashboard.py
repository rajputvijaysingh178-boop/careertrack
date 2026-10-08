"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/ping")
def ping():
    return {"module": "dashboard", "status": "ok"}
