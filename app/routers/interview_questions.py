"""OWNER: M3 (Interview Prep & Intelligence)"""
from fastapi import APIRouter

router = APIRouter(prefix="/interview-questions", tags=["interview_questions"])


@router.get("/ping")
def ping():
    return {"module": "interview_questions", "status": "ok"}
