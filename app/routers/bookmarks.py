"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.bookmark import Bookmark
from app.models.job import Job
from app.schemas.bookmark import BookmarkCreate, BookmarkOut, BookmarkUpdate

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.get("/ping")
def ping():
    return {"module": "bookmarks", "status": "ok"}


@router.get("", response_model=list[BookmarkOut])
def list_bookmarks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Bookmark).filter_by(user_id=user.id).order_by(Bookmark.created_at.desc()).all()


@router.post("", response_model=BookmarkOut, status_code=201)
def save_bookmark(data: BookmarkCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if data.type.upper() not in {"SAVE", "APPLY", "IGNORE"}:
        from fastapi import HTTPException
        raise HTTPException(422, "type must be SAVE, APPLY or IGNORE")
    if not db.get(Job, data.job_id):
        raise NotFoundError("Job")
    item = db.query(Bookmark).filter_by(user_id=user.id, job_id=data.job_id).first()
    if item:
        item.type = data.type.upper()
    else:
        item = Bookmark(user_id=user.id, job_id=data.job_id, type=data.type.upper())
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{bookmark_id}", response_model=BookmarkOut)
def update_bookmark(bookmark_id: int, data: BookmarkUpdate, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    item = db.query(Bookmark).filter_by(id=bookmark_id, user_id=user.id).first()
    if not item:
        raise NotFoundError("Bookmark")
    if data.type.upper() not in {"SAVE", "APPLY", "IGNORE"}:
        from fastapi import HTTPException
        raise HTTPException(422, "type must be SAVE, APPLY or IGNORE")
    item.type = data.type.upper()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.query(Bookmark).filter_by(id=bookmark_id, user_id=user.id).first()
    if not item:
        raise NotFoundError("Bookmark")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
