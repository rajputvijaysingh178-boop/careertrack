"""OWNER: M3 (Interview Prep & Intelligence)"""
from fastapi import APIRouter

router = APIRouter(prefix="/prep", tags=["prep"])


@router.get("/ping")
def ping():
    return {"module": "prep", "status": "ok"}
