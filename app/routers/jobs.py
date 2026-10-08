"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/ping")
def ping():
    return {"module": "jobs", "status": "ok"}
