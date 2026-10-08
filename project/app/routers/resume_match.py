"""OWNER: M3 (Interview Prep & Intelligence)"""
from fastapi import APIRouter

router = APIRouter(prefix="/resume-match", tags=["resume_match"])


@router.get("/ping")
def ping():
    return {"module": "resume_match", "status": "ok"}
