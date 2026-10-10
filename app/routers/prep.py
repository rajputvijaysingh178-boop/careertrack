"""OWNER: M3 - interview prep workspace, skill gap, AI prep plan, analytics"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.prep import PlanRequest
from app.services.interview_analytics_service import InterviewAnalyticsService
from app.services.prep_plan_service import PrepPlanService
from app.services.prep_workspace_service import PrepWorkspaceService
from app.services.skill_gap_service import SkillGapService

router = APIRouter(prefix="/prep", tags=["prep"])


@router.get("/ping")
def ping():
    return {"module": "prep", "status": "ok"}


@router.get("/jobs/{job_id}")
def job_workspace(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Job -> skills -> questions (grouped) -> materials -> blogs."""
    return PrepWorkspaceService(db).build_workspace(job_id=job_id, user=user)


@router.get("/applications/{application_id}")
def application_workspace(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Same as the job workspace, for the user's own application (also returns my questions for it)."""
    return PrepWorkspaceService(db).build_workspace(application_id=application_id, user=user)


@router.get("/jobs/{job_id}/skill-gap")
def job_skill_gap(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return SkillGapService(db).gap(user, job_id=job_id)


@router.get("/applications/{application_id}/skill-gap")
def application_skill_gap(application_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return SkillGapService(db).gap(user, application_id=application_id)


@router.post("/plan")
def prepare_me(body: PlanRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """'Prepare Me for This Job' -> N-day plan from job_id, application_id or pasted jd_text."""
    return PrepPlanService(db).generate(user, job_id=body.job_id, application_id=body.application_id,
                                        jd_text=body.jd_text, days=body.days, use_ai=body.use_ai)


@router.get("/analytics")
def interview_analytics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return InterviewAnalyticsService(db).analytics(user.id)
