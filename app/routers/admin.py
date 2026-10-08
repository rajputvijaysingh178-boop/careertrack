"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def ping():
    return {"module": "admin", "status": "ok"}
