"""OWNER: M1 - job board. Visitors/users see only ACTIVE, non-expired jobs; admins see everything.

Route order: fixed paths (/check-duplicate) before /{job_id}.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_optional_user, require_admin
from app.schemas.job import (DuplicateCheck, JobCreate, JobOut, JobPage, JobSkillsReplace, JobUpdate,
                             ReopenBody, _enum, EMPLOYMENT_TYPES, WORK_MODES)
from app.schemas.material import MaterialOut
from app.services.job_service import JobService
from app.services.material_service import MaterialService

router = APIRouter(prefix="/jobs", tags=["jobs"])
_work_mode = _enum(WORK_MODES, "work_mode")
_employment = _enum(EMPLOYMENT_TYPES, "employment_type")


@router.get("/ping")
def ping():
    return {"module": "jobs", "status": "ok"}


@router.get("", response_model=JobPage)
def search_jobs(
    q: Optional[str] = Query(None, description="title, description, company or skill"),
    location: Optional[str] = None,
    work_mode: Optional[str] = Query(None, description="REMOTE / HYBRID / ONSITE"),
    remote: Optional[bool] = Query(None, description="shortcut for work_mode=REMOTE"),
    experience: Optional[int] = Query(None, ge=0, le=60, description="your years of experience"),
    salary_min: Optional[float] = Query(None, ge=0, description="LPA"),
    salary_max: Optional[float] = Query(None, ge=0, description="LPA"),
    employment_type: Optional[str] = None,
    job_type: Optional[str] = Query(None, description="role family, e.g. Backend, QA, DevOps"),
    company_id: Optional[int] = None,
    skills: Optional[str] = Query(None, description="comma separated, e.g. python,playwright"),
    skills_match: str = Query("any", pattern="^(any|all)$"),
    posted_within_days: Optional[int] = Query(None, ge=0, le=365),
    status: Optional[str] = Query(None, description="admin only"),
    sort: str = Query("newest", pattern="^(newest|salary|expiring)$"),
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user=Depends(get_optional_user),
):
    return JobService(db).list(
        user, skip=skip, limit=limit, q=q, location=location,
        work_mode="REMOTE" if remote else _work_mode(work_mode), experience=experience,
        salary_min=salary_min, salary_max=salary_max, employment_type=_employment(employment_type),
        job_type=job_type, company_id=company_id,
        skill_names=[s for s in (skills or "").split(",") if s.strip()], skills_match=skills_match,
        posted_within_days=posted_within_days, status=status.upper() if status else None, sort=sort)


@router.post("/check-duplicate")
def check_duplicate(body: DuplicateCheck, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Is there a similar job at this company already? (same check that runs on create/publish)"""
    similar = JobService(db).find_similar(body.company_id, body.title, body.description, body.exclude_job_id)
    return {"duplicate": bool(similar), "similar_jobs": similar}


@router.post("", response_model=JobOut, status_code=201)
def create_job(data: JobCreate, force: bool = Query(False, description="skip the duplicate warning"),
               db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Creates the job as DRAFT. Returns 409 with similar_jobs if a similar job exists."""
    return JobService(db).create(admin, data, force)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    return JobService(db).get(user, job_id)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, data: JobUpdate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return JobService(db).update(admin, job_id, data)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """Hard delete. Refused (409) when applications exist: close the job instead."""
    JobService(db).delete(job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{job_id}/skills", response_model=JobOut)
def replace_job_skills(job_id: int, body: JobSkillsReplace, db: Session = Depends(get_db),
                       admin=Depends(require_admin)):
    return JobService(db).replace_skills(job_id, body.skills)


@router.post("/{job_id}/publish", response_model=JobOut)
def publish_job(job_id: int, force: bool = False, db: Session = Depends(get_db), admin=Depends(require_admin)):
    """DRAFT -> ACTIVE (or PUBLISHED when posted_date is in the future)."""
    return JobService(db).publish(job_id, force)


@router.post("/{job_id}/unpublish", response_model=JobOut)
def unpublish_job(job_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return JobService(db).unpublish(job_id)


@router.post("/{job_id}/expire", response_model=JobOut)
def expire_job(job_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return JobService(db).expire(job_id)


@router.post("/{job_id}/close", response_model=JobOut)
def close_job(job_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return JobService(db).close(job_id)


@router.post("/{job_id}/reopen", response_model=JobOut)
def reopen_job(job_id: int, body: ReopenBody = ReopenBody(), db: Session = Depends(get_db),
               admin=Depends(require_admin)):
    """EXPIRED -> ACTIVE, optionally with a new expiry_date."""
    return JobService(db).reopen(job_id, body.expiry_date)


@router.get("/{job_id}/materials", response_model=List[MaterialOut])
def job_materials(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Study materials attached to this job, its company or its skills."""
    return MaterialService(db).for_job(job_id)
