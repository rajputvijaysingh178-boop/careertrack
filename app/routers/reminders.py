"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/ping")
def ping():
    return {"module": "reminders", "status": "ok"}


@router.get("", response_model=list[ReminderOut])
def list_reminders(status: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ReminderService(db).list(user.id, status)


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(data: ReminderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ReminderService(db).create(user.id, data)


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, data: ReminderUpdate, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    return ReminderService(db).update(reminder_id, user.id, data)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ReminderService(db).delete(reminder_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
