"""OWNER: M3 - Resume vs JD match"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.resume_match_service import ResumeMatchService

router = APIRouter(prefix="/resume-match", tags=["resume-match"])

MAX_RESUME_BYTES = 5 * 1024 * 1024


@router.get("/ping")
def ping():
    return {"module": "resume_match", "status": "ok"}


@router.post("")
async def match_resume(
    file: Optional[UploadFile] = File(None, description="PDF, DOCX or TXT resume"),
    resume_text: Optional[str] = Form(None, description="Alternative to uploading a file"),
    job_id: Optional[int] = Form(None),
    application_id: Optional[int] = Form(None),
    jd_text: Optional[str] = Form(None, description="Paste a JD instead of using job_id"),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    content, filename = None, None
    if file is not None and file.filename:
        content = await file.read(MAX_RESUME_BYTES + 1)
        filename = file.filename
        if len(content) > MAX_RESUME_BYTES:
            from fastapi import HTTPException
            raise HTTPException(413, "Resume file is larger than 5 MB")
    return ResumeMatchService(db).match(user, filename=filename, content=content, resume_text=resume_text,
                                        job_id=job_id, application_id=application_id, jd_text=jd_text)


@router.get("/history")
def history(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ResumeMatchService(db).history(user.id, limit)
