"""OWNER: M3 - resolves "what are we preparing for?" from a job, application or custom role.

Used by the prep workspace, skill gap, resume match and prep plan so they share target resolution.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.jd_parser import analyze_jd
from app.core.exceptions import NotFoundError
from app.repositories.prep_lookup_repository import PrepLookupRepository


def is_admin(user) -> bool:
    return str(getattr(user, "role", "")).upper() == "ADMIN"


def resolve_target(db: Session, user, job_id: Optional[int] = None, application_id: Optional[int] = None,
                   jd_text: Optional[str] = None, role_title: Optional[str] = None) -> dict:
    """Return target identifiers, display metadata, source text and extracted skills."""
    lookup = PrepLookupRepository(db)
    company_id = None
    application = None

    if application_id is not None:
        application = lookup.get_application(application_id)
        if not application or (application.get("user_id") != user.id and not is_admin(user)):
            raise NotFoundError("Application")  # same 404 for "not yours" so ids don't leak
        job_id = job_id or application.get("job_id")
        company_id = application.get("company_id")
        jd_text = jd_text or application.get("jd_text") or application.get("job_title")

    job = lookup.get_job(job_id) if job_id else None
    if job_id and not job and not jd_text:
        raise NotFoundError("Job")
    if job:
        company_id = job.get("company_id") or company_id

    resolved_title = (job.get("title") if job else None) or \
        (application.get("job_title") if application else None) or role_title
    if not (job or jd_text or resolved_title):
        raise HTTPException(400, "Provide job_id, application_id, role_title or jd_text")

    if application and not job:
        source_text = "\n".join(part for part in (
            application.get("job_title"), application.get("skills"), application.get("requirements"),
            application.get("jd_text"),
        ) if part)
    else:
        source_text = jd_text or (job.get("description") if job else "") or resolved_title or ""

    skills = [{"name": item["name"], "importance": item.get("importance") or "REQUIRED"}
              for item in (lookup.job_skills(job_id) if job and job_id else [])]
    if not skills and source_text:
        skills = [{"name": item["name"], "importance": item["importance"]}
                  for item in analyze_jd(source_text, lookup.skill_names())["skills"]]

    display_job = job
    if not display_job and resolved_title:
        display_job = {
            "id": job_id,
            "title": resolved_title,
            "company_id": company_id,
            "company_name": application.get("company_name") if application else None,
            "description": source_text,
        }

    return {"job": display_job, "job_id": job_id, "application_id": application_id,
            "company_id": company_id, "role_title": resolved_title,
            "jd_text": source_text, "skills": skills}
