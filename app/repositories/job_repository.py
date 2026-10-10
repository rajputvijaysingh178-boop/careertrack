"""OWNER: M1 - DB access for jobs and job_skills: search/filters, expiry queries (no business rules)."""
import logging
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import and_, func, inspect, or_, select, text, update
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job
from app.models.material import Material
from app.models.skill import JobSkill, Skill

log = logging.getLogger(__name__)


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------- basic
    def get(self, job_id: int) -> Optional[Job]:
        return self.db.get(Job, job_id)

    def add(self, job: Job) -> Job:
        """Adds and flushes (no commit); the service commits once at the end."""
        self.db.add(job)
        self.db.flush()
        return job

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def delete(self, job: Job) -> None:
        self.db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
        self.db.delete(job)

    # ---------------------------------------------------------------- skills
    def set_skills(self, job_id: int, skills: Iterable[Tuple[int, str]]) -> None:
        self.db.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
        for skill_id, importance in skills:
            self.db.add(JobSkill(job_id=job_id, skill_id=skill_id, importance=importance))
        self.db.flush()

    def skills_for_jobs(self, job_ids: Iterable[int]) -> Dict[int, List[dict]]:
        ids = list(job_ids)
        out: Dict[int, List[dict]] = {i: [] for i in ids}
        if not ids:
            return out
        rows = (self.db.query(JobSkill.job_id, Skill.id, Skill.name, JobSkill.importance)
                .join(Skill, Skill.id == JobSkill.skill_id).filter(JobSkill.job_id.in_(ids))
                .order_by(JobSkill.importance, Skill.name).all())
        for job_id, sid, name, importance in rows:
            out[job_id].append({"id": sid, "name": name, "importance": importance})
        return out

    def skill_ids(self, job_id: int) -> List[int]:
        return [sid for (sid,) in self.db.query(JobSkill.skill_id).filter(JobSkill.job_id == job_id).all()]

    # ---------------------------------------------------------------- search
    def search(self, *, public: bool, q: Optional[str] = None, location: Optional[str] = None,
               work_mode: Optional[str] = None, experience: Optional[int] = None,
               salary_min: Optional[float] = None, salary_max: Optional[float] = None,
               employment_type: Optional[str] = None, job_type: Optional[str] = None,
               company_id: Optional[int] = None, skill_names: Optional[List[str]] = None,
               skills_match: str = "any", posted_within_days: Optional[int] = None,
               status: Optional[str] = None, sort: str = "newest", skip: int = 0, limit: int = 20
               ) -> Tuple[List[Job], int]:
        J = Job
        today = date.today()
        query = self.db.query(J)

        if public:   # visitors / normal users only ever see live, non-expired jobs
            query = query.filter(J.status == "ACTIVE", or_(J.expiry_date.is_(None), J.expiry_date >= today))
        elif status:
            query = query.filter(J.status == status)

        if q:
            like = f"%{q}%"
            by_skill = select(JobSkill.job_id).join(Skill, Skill.id == JobSkill.skill_id).where(Skill.name.ilike(like))
            by_company = select(Company.id).where(Company.name.ilike(like))
            query = query.filter(or_(J.title.ilike(like), J.description.ilike(like),
                                     J.company_id.in_(by_company), J.id.in_(by_skill)))
        if location:
            query = query.filter(J.location.ilike(f"%{location}%"))
        if work_mode:
            query = query.filter(J.work_mode == work_mode)
        if employment_type:
            query = query.filter(J.employment_type == employment_type)
        if job_type:
            query = query.filter(func.lower(J.job_type) == job_type.lower())
        if company_id is not None:
            query = query.filter(J.company_id == company_id)
        if experience is not None:     # jobs whose experience range contains this many years (open ends allowed)
            query = query.filter(and_(or_(J.experience_min.is_(None), J.experience_min <= experience),
                                      or_(J.experience_max.is_(None), J.experience_max >= experience)))
        if salary_min is not None:     # salary ranges that overlap [salary_min, salary_max]
            query = query.filter(or_(J.salary_max.is_(None), J.salary_max >= salary_min))
        if salary_max is not None:
            query = query.filter(or_(J.salary_min.is_(None), J.salary_min <= salary_max))
        if posted_within_days is not None:
            query = query.filter(J.posted_date >= today - timedelta(days=posted_within_days))

        names = [n.strip().lower() for n in (skill_names or []) if n and n.strip()]
        if names:
            wanted = select(Skill.id).where(func.lower(Skill.name).in_(names))
            if skills_match == "all":
                all_ids = (select(JobSkill.job_id).where(JobSkill.skill_id.in_(wanted)).group_by(JobSkill.job_id)
                           .having(func.count(func.distinct(JobSkill.skill_id)) >= len(set(names))))
                query = query.filter(J.id.in_(all_ids))
            else:
                query = query.filter(J.id.in_(select(JobSkill.job_id).where(JobSkill.skill_id.in_(wanted))))

        total = query.count()
        if sort == "salary":
            query = query.order_by(J.salary_max.desc(), J.id.desc())
        elif sort == "expiring":
            query = query.order_by(J.expiry_date.asc(), J.id.desc())
        else:
            query = query.order_by(J.posted_date.desc(), J.id.desc())
        return query.offset(skip).limit(limit).all(), total

    # ---------------------------------------------------------------- duplicate detection
    def similar_candidates(self, company_id: int, exclude_id: Optional[int] = None) -> List[Job]:
        """Same-company jobs that could be duplicates (not expired / closed)."""
        query = self.db.query(Job).filter(Job.company_id == company_id,
                                          Job.status.in_(("DRAFT", "PUBLISHED", "ACTIVE")))
        if exclude_id is not None:
            query = query.filter(Job.id != exclude_id)
        return query.all()

    # ---------------------------------------------------------------- expiry maintenance (scheduled task)
    def activate_scheduled(self, today: date) -> int:
        res = self.db.execute(update(Job).where(Job.status == "PUBLISHED", Job.posted_date <= today)
                              .values(status="ACTIVE").execution_options(synchronize_session=False))
        self.db.commit()
        return res.rowcount or 0

    def expire_overdue(self, today: date) -> int:
        """expiry_date < today  =>  EXPIRED  (the business rule from the project document)."""
        res = self.db.execute(update(Job).where(Job.status.in_(("ACTIVE", "PUBLISHED")), Job.expiry_date < today)
                              .values(status="EXPIRED").execution_options(synchronize_session=False))
        self.db.commit()
        return res.rowcount or 0

    # ---------------------------------------------------------------- deleting
    def _has_table(self, name: str) -> bool:
        try:
            return inspect(self.db.get_bind()).has_table(name)
        except Exception:
            return False

    def applications_count(self, job_id: int) -> int:
        """Applications (M2's table) that point at this job. 0 if the table doesn't exist yet."""
        if not self._has_table("applications"):
            return 0
        return self.db.execute(text("SELECT COUNT(*) FROM applications WHERE job_id = :j"), {"j": job_id}).scalar() or 0

    def detach_references(self, job_id: int) -> None:
        """Clear links to a job that is about to be deleted (only for tables that exist)."""
        self.db.query(Material).filter(Material.job_id == job_id).update({"job_id": None})
        for table, sql in (("bookmarks", "DELETE FROM bookmarks WHERE job_id = :j"),
                           ("interview_questions", "UPDATE interview_questions SET job_id = NULL WHERE job_id = :j"),
                           ("resume_matches", "UPDATE resume_matches SET job_id = NULL WHERE job_id = :j")):
            if self._has_table(table):
                self.db.execute(text(sql), {"j": job_id})

    # ---------------------------------------------------------------- reporting
    def count_by_status(self) -> Dict[str, int]:
        return {s: n for s, n in self.db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()}

    def count_by(self, column) -> Dict[str, int]:
        rows = self.db.query(column, func.count(Job.id)).group_by(column).all()
        return {(k or "Unspecified"): n for k, n in rows}

    def top_companies(self, limit: int = 10) -> List[dict]:
        rows = (self.db.query(Company.name, func.count(Job.id)).join(Job, Job.company_id == Company.id)
                .group_by(Company.name).order_by(func.count(Job.id).desc()).limit(limit).all())
        return [{"company": n, "jobs": c} for n, c in rows]

    def posted_dates(self) -> List[date]:
        return [d for (d,) in self.db.query(Job.posted_date).filter(Job.posted_date.isnot(None)).all()]
