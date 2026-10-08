"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/ping")
def ping():
    return {"module": "bookmarks", "status": "ok"}
