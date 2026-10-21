"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/ping")
def ping():
    return {"module": "dashboard", "status": "ok"}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return AnalyticsService(db).summary(user.id)
