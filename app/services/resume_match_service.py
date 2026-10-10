"""OWNER: M3
Responsibility: Resume vs Job Description match (percentage, matched skills, missing skills, tips).
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.matching import match_skills
from app.ai.resume_parser import extract_text
from app.ai.skill_extractor import extract_skills
from app.repositories.prep_lookup_repository import PrepLookupRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.services.prep_target import resolve_target


class ResumeMatchService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)
        self.history_repo = UserSkillRepository(db)

    def match(self, user, *, filename: Optional[str] = None, content: Optional[bytes] = None,
              resume_text: Optional[str] = None, job_id: Optional[int] = None,
              application_id: Optional[int] = None, jd_text: Optional[str] = None) -> dict:
        if content:
            try:
                resume_text = extract_text(filename or "", content)
            except ValueError as exc:
                raise HTTPException(400, str(exc))
            except Exception:
                raise HTTPException(400, "Could not read the resume file")
        if not resume_text or not resume_text.strip():
            raise HTTPException(400, "Upload a resume file or provide resume_text")

        target = resolve_target(self.db, user, job_id, application_id, jd_text)
        if not target["skills"]:
            raise HTTPException(400, "No skills could be found for this job / JD")

        resume_skills = extract_skills(resume_text, self.lookup.skill_names())
        result = match_skills(target["skills"], resume_skills)
        result["resume_skills"] = resume_skills
        result["job"] = ({"id": target["job"]["id"], "title": target["job"].get("title"),
                          "company": target["job"].get("company_name")} if target["job"] else None)

        self.history_repo.add_match(user_id=user.id, job_id=target["job_id"], application_id=application_id,
                                    resume_filename=filename, match_percent=result["match_percent"],
                                    matched=[m["name"] for m in result["matched"]],
                                    missing=[m["name"] for m in result["missing"]])
        return result

    def history(self, user_id: int, limit: int = 20) -> list:
        return [{"id": r.id, "job_id": r.job_id, "application_id": r.application_id,
                 "resume_filename": r.resume_filename, "match_percent": r.match_percent,
                 "matched": r.matched or [], "missing": r.missing or [],
                 "created_at": r.created_at.isoformat() if r.created_at else None}
                for r in self.history_repo.match_history(user_id, limit)]
