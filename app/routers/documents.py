"""OWNER: M2 (Application Tracker)"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.application import Application
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/ping")
def ping():
    return {"module": "documents", "status": "ok"}


@router.get("", response_model=list[DocumentOut])
def list_documents(application_id: int | None = None, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    q = db.query(Document).filter_by(user_id=user.id)
    if application_id is not None:
        if not db.query(Application.id).filter_by(id=application_id, user_id=user.id).first():
            raise NotFoundError("Application")
        q = q.filter_by(application_id=application_id)
    return q.order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(data: DocumentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not db.query(Application.id).filter_by(id=data.application_id, user_id=user.id).first():
        raise NotFoundError("Application")
    item = Document(user_id=user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.query(Document).filter_by(id=document_id, user_id=user.id).first()
    if not item:
        raise NotFoundError("Document")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
