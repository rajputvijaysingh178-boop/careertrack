"""OWNER: M3 - resolves "what are we preparing for?" from a job_id, an application_id or pasted JD text.

Used by the prep workspace, skill gap, resume match and prep plan so they all behave the same way.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.jd_parser import analyze_jd
from app.core.exceptions import NotFoundError
from app.repositories.prep_lookup_repository import PrepLookupRepository


def is_admin(user) -> bool:
    return str(getattr(user, "role", "")).upper().endswith("ADMIN")


def resolve_target(db: Session, user, job_id: Optional[int] = None, application_id: Optional[int] = None,
                   jd_text: Optional[str] = None) -> dict:
    """Return {job, job_id, application_id, company_id, role_title, jd_text, skills[{name, importance}]}."""
    lookup = PrepLookupRepository(db)
    company_id = None

    if application_id is not None:
        app = lookup.get_application(application_id)
        if not app or (app.get("user_id") != user.id and not is_admin(user)):
            raise NotFoundError("Application")       # same 404 for "not yours" so ids don't leak
        job_id = job_id or app.get("job_id")
        company_id = app.get("company_id")
        jd_text = jd_text or app.get("jd_text")       # the exact JD snapshot saved by M2, if available

    job = lookup.get_job(job_id) if job_id else None
    if job_id and not job and not jd_text:
        raise NotFoundError("Job")
    if job:
        company_id = job.get("company_id") or company_id

    if not (job or jd_text):
        raise HTTPException(400, "Provide job_id, application_id or jd_text")

    skills = [{"name": s["name"], "importance": s.get("importance") or "REQUIRED"}
              for s in (lookup.job_skills(job_id) if job else [])]
    text = jd_text or (job.get("description") if job else "") or ""
    if not skills and text:                            # no skills saved by admin -> extract from the JD text
        skills = [{"name": s["name"], "importance": s["importance"]}
                  for s in analyze_jd(text, lookup.skill_names())["skills"]]

    return {"job": job, "job_id": job_id, "application_id": application_id, "company_id": company_id,
            "role_title": job.get("title") if job else None, "jd_text": text, "skills": skills}
