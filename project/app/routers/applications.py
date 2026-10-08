"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/ping")
def ping():
    return {"module": "applications", "status": "ok"}
