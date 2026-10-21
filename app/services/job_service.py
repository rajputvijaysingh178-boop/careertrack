"""OWNER: M1
Responsibility: jobs - CRUD, search/filters, publish / expire / close / reopen workflow, duplicate detection,
automatic expiry. Business rules live here; DB access is in JobRepository.
"""
from datetime import date
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import is_admin
from app.core.exceptions import NotFoundError
from app.models.job import Job
from app.models.skill import Skill
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_repository import JobRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.job import JobCreate, JobSkillIn, JobUpdate
from app.workflows.duplicate_detection import compare
from app.workflows.job_status import validate_transition

_REQUIRED_COLUMNS = ("title", "description", "company_id")


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobRepository(db)
        self.companies = CompanyRepository(db)
        self.skills = SkillRepository(db)

    # ================================================================ helpers
    def _get(self, job_id: int) -> Job:
        job = self.repo.get(job_id)
        if not job:
            raise NotFoundError("Job")
        return job

    def _active_company(self, company_id: int):
        company = self.companies.get(company_id)
        if not company:
            raise HTTPException(400, f"Company {company_id} does not exist")
        if company.status != "ACTIVE":
            raise HTTPException(400, "This company is INACTIVE")
        return company

    def _resolve_skills(self, items: List[JobSkillIn]) -> list:
        """-> [(skill_id, importance)]. Unknown skill names are added to the skills table."""
        resolved = {}
        for item in items:
            if item.skill_id is not None:
                skill = self.skills.get(item.skill_id)
                if not skill:
                    raise HTTPException(400, f"Skill {item.skill_id} does not exist")
            else:
                skill = self.skills.get_by_name(item.name) or self.skills.add(Skill(name=item.name.strip(), category="Other"))
            resolved[skill.id] = item.importance
        return list(resolved.items())

    def _serialize(self, jobs: List[Job], detail: bool = False) -> List[dict]:
        companies = self.companies.get_many([j.company_id for j in jobs])
        skills = self.repo.skills_for_jobs([j.id for j in jobs])
        today = date.today()
        out = []
        for j in jobs:
            c = companies.get(j.company_id)
            out.append({
                "id": j.id,
                "company": {"id": c.id, "name": c.name, "logo_url": c.logo_url} if c else None,
                "title": j.title, "description": j.description if detail else None,
                "location": j.location, "work_mode": j.work_mode, "employment_type": j.employment_type,
                "job_type": j.job_type, "experience_min": j.experience_min, "experience_max": j.experience_max,
                "salary_min": j.salary_min, "salary_max": j.salary_max, "application_url": j.application_url,
                "posted_date": j.posted_date, "expiry_date": j.expiry_date,
                "posted_days_ago": (today - j.posted_date).days if j.posted_date else None,
                "is_expired": bool(j.expiry_date and j.expiry_date < today),
                "status": j.status, "skills": skills.get(j.id, []), "created_by": j.created_by,
                "created_at": j.created_at})
        return out

    @staticmethod
    def _visible(job: Job, user) -> bool:
        if is_admin(user):
            return True
        return job.status == "ACTIVE" and not (job.expiry_date and job.expiry_date < date.today())

    # ================================================================ duplicate detection
    def find_similar(self, company_id: int, title: str, description: Optional[str],
                     exclude_id: Optional[int] = None) -> list:
        found = []
        for other in self.repo.similar_candidates(company_id, exclude_id):
            cmp = compare(title, description or "", other.title, other.description or "")
            if cmp["duplicate"]:
                found.append({"id": other.id, "title": other.title, "status": other.status,
                              "title_similarity": cmp["title_similarity"],
                              "description_similarity": cmp["description_similarity"], "score": cmp["score"]})
        return sorted(found, key=lambda d: -d["score"])

    def _check_duplicates(self, company_id, title, description, exclude_id, force: bool) -> None:
        if force:
            return
        similar = self.find_similar(company_id, title, description, exclude_id)
        if similar:
            raise HTTPException(409, detail={
                "message": "A similar active job already exists.", "similar_jobs": similar,
                "hint": "Repeat the request with ?force=true if this is really a different job."})

    # ================================================================ read
    def get(self, user, job_id: int) -> dict:
        job = self._get(job_id)
        if not self._visible(job, user):
            raise NotFoundError("Job")
        return self._serialize([job], detail=True)[0]

    def list(self, user, *, skip: int = 0, limit: int = 20, **filters) -> dict:
        admin = is_admin(user)
        if not admin:
            filters["status"] = None
        jobs, total = self.repo.search(public=not admin, skip=skip, limit=limit, **filters)
        return {"items": self._serialize(jobs), "total": total, "skip": skip, "limit": limit}

    # ================================================================ write
    def create(self, user, data: JobCreate, force: bool = False) -> dict:
        self._active_company(data.company_id)
        self._check_duplicates(data.company_id, data.title, data.description, None, force)
        job = Job(company_id=data.company_id, title=data.title.strip(), description=data.description,
                  location=data.location, work_mode=data.work_mode, employment_type=data.employment_type,
                  job_type=data.job_type, experience_min=data.experience_min, experience_max=data.experience_max,
                  salary_min=data.salary_min, salary_max=data.salary_max, application_url=data.application_url,
                  posted_date=data.posted_date, expiry_date=data.expiry_date, status="DRAFT", created_by=user.id)
        self.repo.add(job)
        self.repo.set_skills(job.id, self._resolve_skills(data.skills))
        self.repo.commit()
        self.repo.refresh(job)
        return self._serialize([job], detail=True)[0]

    def update(self, user, job_id: int, data: JobUpdate) -> dict:
        job = self._get(job_id)
        fields = data.model_dump(exclude_unset=True, exclude={"skills"})
        for key in _REQUIRED_COLUMNS:                    # NOT NULL columns can't be cleared
            if key in fields and fields[key] is None:
                fields.pop(key)
        if "company_id" in fields:
            self._active_company(fields["company_id"])
        merged = lambda k: fields[k] if k in fields else getattr(job, k)
        if merged("experience_min") is not None and merged("experience_max") is not None \
                and merged("experience_min") > merged("experience_max"):
            raise HTTPException(400, "experience_min cannot be greater than experience_max")
        if merged("salary_min") is not None and merged("salary_max") is not None \
                and merged("salary_min") > merged("salary_max"):
            raise HTTPException(400, "salary_min cannot be greater than salary_max")
        for key, value in fields.items():
            setattr(job, key, value.strip() if key == "title" and isinstance(value, str) else value)
        if data.skills is not None:
            self.repo.set_skills(job.id, self._resolve_skills(data.skills))
        self.repo.commit()
        self.repo.refresh(job)
        return self._serialize([job], detail=True)[0]

    def replace_skills(self, job_id: int, items: List[JobSkillIn]) -> dict:
        job = self._get(job_id)
        self.repo.set_skills(job.id, self._resolve_skills(items))
        self.repo.commit()
        return self._serialize([job], detail=True)[0]

    def delete(self, job_id: int) -> None:
        job = self._get(job_id)
        n = self.repo.applications_count(job.id)
        if n:
            raise HTTPException(409, f"{n} application(s) exist for this job. Close it instead "
                                     f"(POST /jobs/{job.id}/close). Applications keep their own JD snapshot.")
        self.repo.detach_references(job.id)
        self.repo.delete(job)
        self.repo.commit()

    # ================================================================ status workflow
    def _move(self, job: Job, new_status: str) -> dict:
        validate_transition(job.status, new_status)
        job.status = new_status
        self.repo.commit()
        self.repo.refresh(job)
        return self._serialize([job], detail=True)[0]

    def publish(self, job_id: int, force: bool = False) -> dict:
        job = self._get(job_id)
        if job.status != "DRAFT":
            raise HTTPException(400, f"Only DRAFT jobs can be published (this job is {job.status}). "
                                     f"Use /reopen for an expired job.")
        self._active_company(job.company_id)
        today = date.today()
        if job.expiry_date and job.expiry_date < today:
            raise HTTPException(400, "expiry_date is in the past. Update it before publishing.")
        self._check_duplicates(job.company_id, job.title, job.description, job.id, force)
        job.posted_date = job.posted_date or today
        return self._move(job, "ACTIVE" if job.posted_date <= today else "PUBLISHED")

    def unpublish(self, job_id: int) -> dict:
        return self._move(self._get(job_id), "DRAFT")

    def expire(self, job_id: int) -> dict:
        return self._move(self._get(job_id), "EXPIRED")

    def close(self, job_id: int) -> dict:
        return self._move(self._get(job_id), "CLOSED")

    def reopen(self, job_id: int, expiry_date: Optional[date] = None) -> dict:
        job = self._get(job_id)
        if job.status != "EXPIRED":
            raise HTTPException(400, "Only EXPIRED jobs can be reopened")
        new_expiry = expiry_date or job.expiry_date
        if new_expiry and new_expiry < date.today():
            raise HTTPException(400, "Provide a new expiry_date in the future")
        job.expiry_date = new_expiry
        return self._move(job, "ACTIVE")

    # ================================================================ scheduled maintenance
    def run_maintenance(self, today: Optional[date] = None) -> dict:
        """PUBLISHED jobs whose posted_date arrived -> ACTIVE;  expiry_date < today -> EXPIRED."""
        today = today or date.today()
        activated = self.repo.activate_scheduled(today)
        expired = self.repo.expire_overdue(today)
        return {"activated": activated, "expired": expired}
