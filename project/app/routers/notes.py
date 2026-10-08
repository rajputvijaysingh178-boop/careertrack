"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/ping")
def ping():
    return {"module": "notes", "status": "ok"}
