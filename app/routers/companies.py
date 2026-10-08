"""OWNER: M1 (Job Board & Admin)"""
from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/ping")
def ping():
    return {"module": "companies", "status": "ok"}
