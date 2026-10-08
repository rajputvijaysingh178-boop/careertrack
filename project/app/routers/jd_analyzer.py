"""OWNER: M3 (Interview Prep & Intelligence)"""
from fastapi import APIRouter

router = APIRouter(prefix="/jd-analyzer", tags=["jd_analyzer"])


@router.get("/ping")
def ping():
    return {"module": "jd_analyzer", "status": "ok"}
