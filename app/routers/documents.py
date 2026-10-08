"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/ping")
def ping():
    return {"module": "documents", "status": "ok"}
