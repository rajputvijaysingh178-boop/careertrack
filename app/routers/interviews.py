"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.interview import InterviewCreate, InterviewOut, InterviewUpdate
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("/ping")
def ping():
    return {"module": "interviews", "status": "ok"}


@router.get("/applications/{application_id}", response_model=list[InterviewOut])
def list_interviews(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return InterviewService(db).list_for_application(application_id, user.id)


@router.post("/applications/{application_id}", response_model=InterviewOut, status_code=201)
def create_interview(application_id: int, data: InterviewCreate, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return InterviewService(db).create(application_id, user.id, data)


@router.put("/{interview_id}", response_model=InterviewOut)
def update_interview(interview_id: int, data: InterviewUpdate, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return InterviewService(db).update(interview_id, user.id, data)


@router.get("/{interview_id}/history")
def interview_history(interview_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{"id": h.id, "interview_id": h.interview_id, "old_status": h.old_status,
             "new_status": h.new_status, "round_name": h.round_name, "scheduled_at": h.scheduled_at,
             "mode": h.mode, "interviewer": h.interviewer, "meeting_link": h.meeting_link,
             "changed_at": h.changed_at, "feedback": h.feedback}
            for h in InterviewService(db).history(interview_id, user.id)]


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    InterviewService(db).delete(interview_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
