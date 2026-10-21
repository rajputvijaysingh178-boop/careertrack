"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services.notes_service import NotesService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/ping")
def ping():
    return {"module": "notes", "status": "ok"}


@router.get("", response_model=list[NoteOut])
def list_notes(application_id: int | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return NotesService(db).list(user.id, application_id)


@router.post("", response_model=NoteOut, status_code=201)
def create_note(data: NoteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return NotesService(db).create(user.id, data)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return NotesService(db).update(note_id, user.id, data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    NotesService(db).delete(note_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
