"""OWNER: M3 - JD Analyzer endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.prep import JDAnalyzeRequest
from app.services.jd_analyzer_service import JDAnalyzerService

router = APIRouter(prefix="/jd-analyzer", tags=["jd-analyzer"])


@router.get("/ping")
def ping():
    return {"module": "jd_analyzer", "status": "ok"}


@router.post("/analyze")
def analyze_text(body: JDAnalyzeRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Paste a JD -> skills (required/preferred), experience, tools, responsibilities, interview topics."""
    return JDAnalyzerService(db).analyze(body.jd_text, body.use_ai)


@router.get("/job/{job_id}")
def analyze_job(job_id: int, use_ai: bool = False, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Analyze the JD of a job already stored on the platform."""
    return JDAnalyzerService(db).analyze_job(job_id, use_ai)
