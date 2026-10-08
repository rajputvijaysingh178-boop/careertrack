"""OWNER: M3 (Interview Prep & Intelligence)"""
from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/ping")
def ping():
    return {"module": "recommendations", "status": "ok"}
