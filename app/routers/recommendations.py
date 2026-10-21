"""OWNER: M3 - rule-based recommendations"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.prep import MySkillsUpdate
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/ping")
def ping():
    return {"module": "recommendations", "status": "ok"}


@router.get("/my-skills")
def get_my_skills(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"skills": RecommendationService(db).my_skills(user.id)}


@router.put("/my-skills")
def set_my_skills(body: MySkillsUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Replace the user's skill profile. Names that don't exist in the skills table come back in `unknown`."""
    return RecommendationService(db).set_my_skills(user.id, body.skills)


@router.get("/jobs")
def recommended_jobs(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return RecommendationService(db).recommend_jobs(user.id, limit)


@router.get("/job/{job_id}/content")
def related_content(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """'7 blogs, 23 questions, 5 materials' style summary for a job."""
    return RecommendationService(db).content_for_job(job_id, user)
