"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate, HistoryOut, StatusChange
from app.schemas.application_event import ApplicationEventCreate, ApplicationEventOut, HRCallCreate, HRCallOut
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/ping")
def ping():
    return {"module": "applications", "status": "ok"}


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).create(user.id, data)


@router.get("", response_model=list[ApplicationOut])
def list_applications(status: str | None = None, skip: int = Query(0, ge=0),
                      limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    return ApplicationService(db).list(user.id, status, skip, limit)


@router.get("/kanban")
def kanban_board(db: Session = Depends(get_db), user=Depends(get_current_user)):
    statuses = ["SAVED", "APPLIED", "APPLICATION_VIEWED", "SHORTLISTED", "HR_CONTACTED",
                "INTERVIEW_SCHEDULED", "INTERVIEW_1", "INTERVIEW_2", "HR_ROUND", "ON_HOLD",
                "OFFER_RECEIVED", "ACCEPTED", "DECLINED", "REJECTED"]
    items = ApplicationService(db).list(user.id, limit=1000)
    return {status: [ApplicationOut.model_validate(a) for a in items if a.status == status] for status in statuses}


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).get(application_id, user.id)


@router.put("/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, data: ApplicationUpdate, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    return ApplicationService(db).update(application_id, user.id, data)


@router.post("/{application_id}/status", response_model=ApplicationOut)
def change_status(application_id: int, data: StatusChange, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    return ApplicationService(db).change_status(application_id, user.id, data.status, data.comment)


@router.get("/{application_id}/history", response_model=list[HistoryOut])
def application_history(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).history(application_id, user.id)


@router.get("/{application_id}/events", response_model=list[ApplicationEventOut])
def list_application_events(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).events(application_id, user.id)


@router.post("/{application_id}/events", response_model=ApplicationEventOut, status_code=201)
def create_application_event(application_id: int, data: ApplicationEventCreate,
                             db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).add_event(application_id, user.id, data)


@router.get("/{application_id}/hr-calls", response_model=list[HRCallOut])
def list_hr_calls(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).hr_calls(application_id, user.id)


@router.post("/{application_id}/hr-calls", response_model=HRCallOut, status_code=201)
def create_hr_call(application_id: int, data: HRCallCreate,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ApplicationService(db).add_hr_call(application_id, user.id, data)


@router.get("/{application_id}/timeline")
def timeline(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service = ApplicationService(db)
    app = service.get(application_id, user.id)
    history = service.history(application_id, user.id)
    from app.services.interview_service import InterviewService
    interview_service = InterviewService(db)
    rounds = interview_service.list_for_application(application_id, user.id)
    manual_events = service.events(application_id, user.id)
    hr_calls = service.hr_calls(application_id, user.id)
    events = [{"type": "status", **HistoryOut.model_validate(h).model_dump(mode="json")} for h in history]
    for item in rounds:
        changes = interview_service.history(item.id, user.id)
        events.extend({"type": "interview", "id": item.id, "round_name": change.round_name,
                       "scheduled_at": change.scheduled_at,
                       "mode": change.mode, "interviewer": change.interviewer,
                       "meeting_link": change.meeting_link, "status": change.new_status,
                       "old_status": change.old_status, "changed_at": change.changed_at,
                       "feedback": change.feedback}
                      for change in changes)
    events.extend({"type": "note", "id": event.id, "title": event.title, "details": event.details,
                   "changed_at": event.event_at} for event in manual_events)
    events.extend({"type": "hr_call", "id": call.id, "title": "HR call",
                   "details": call.discussion or call.notes, "hr_name": call.hr_name,
                   "next_round": call.next_round, "interview_at": call.interview_at,
                   "changed_at": call.call_at} for call in hr_calls)
    events.sort(key=lambda event: str(event.get("changed_at") or event.get("scheduled_at") or app.created_at))
    return {"application": ApplicationOut.model_validate(app), "events": events}
