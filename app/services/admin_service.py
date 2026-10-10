"""OWNER: M1
Responsibility: admin dashboard numbers and reports.
Counts for M2/M3 tables use plain SQL and return 0 when those tables don't exist yet.
"""
from collections import Counter
from typing import Optional

from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session

from app.models.blog import Blog
from app.models.company import Company
from app.models.job import Job
from app.models.material import Material
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.jobs = JobRepository(db)

    def _count(self, sql: str) -> int:
        table = sql.split("FROM")[1].split()[0]
        try:
            if not inspect(self.db.get_bind()).has_table(table):
                return 0
            return self.db.execute(text(sql)).scalar() or 0
        except Exception:
            self.db.rollback()
            return 0

    def dashboard(self) -> dict:
        by_status = self.jobs.count_by_status()
        return {
            "users": {"total": self.users.count(), "admins": self.users.count(role="ADMIN"),
                      "blocked": self.users.count(status="BLOCKED")},
            "jobs": {"total": sum(by_status.values()), "active": by_status.get("ACTIVE", 0),
                     "draft": by_status.get("DRAFT", 0), "expired": by_status.get("EXPIRED", 0),
                     "closed": by_status.get("CLOSED", 0), "published": by_status.get("PUBLISHED", 0)},
            "companies": self.db.query(func.count(Company.id)).scalar() or 0,
            "applications": self._count("SELECT COUNT(*) FROM applications"),
            "interviews_tracked": self._count("SELECT COUNT(*) FROM interviews"),
            "offers_recorded": self._count("SELECT COUNT(*) FROM applications WHERE status IN "
                                           "('OFFER_RECEIVED','ACCEPTED','DECLINED')"),
            "interview_questions": self._count("SELECT COUNT(*) FROM interview_questions"),
            "materials": self.db.query(func.count(Material.id)).scalar() or 0,
            "blogs": {"total": self.db.query(func.count(Blog.id)).scalar() or 0,
                      "published": self.db.query(func.count(Blog.id)).filter(Blog.status == "PUBLISHED").scalar() or 0},
        }

    def reports(self) -> dict:
        per_month = Counter(d.strftime("%Y-%m") for d in self.jobs.posted_dates())
        return {
            "jobs_by_status": self.jobs.count_by_status(),
            "jobs_by_type": self.jobs.count_by(Job.job_type),
            "jobs_by_work_mode": self.jobs.count_by(Job.work_mode),
            "jobs_by_employment_type": self.jobs.count_by(Job.employment_type),
            "top_companies": self.jobs.top_companies(10),
            "jobs_posted_per_month": dict(sorted(per_month.items())),
            "applications_by_status": self._applications_by_status(),
        }

    def _applications_by_status(self) -> dict:
        try:
            if not inspect(self.db.get_bind()).has_table("applications"):
                return {}
            rows = self.db.execute(text("SELECT status, COUNT(*) AS n FROM applications GROUP BY status"))
            return {r[0]: r[1] for r in rows}
        except Exception:
            self.db.rollback()
            return {}
