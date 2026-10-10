"""OWNER: M1 - DB access for companies"""
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, company_id: int) -> Optional[Company]:
        return self.db.get(Company, company_id)

    def get_many(self, ids: Iterable[int]) -> Dict[int, Company]:
        ids = list(set(ids))
        if not ids:
            return {}
        return {c.id: c for c in self.db.query(Company).filter(Company.id.in_(ids)).all()}

    def get_by_name(self, name: str) -> Optional[Company]:
        return self.db.query(Company).filter(func.lower(Company.name) == name.strip().lower()).first()

    def add(self, obj: Company) -> Company:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def delete(self, obj: Company) -> None:
        self.db.delete(obj)
        self.db.commit()

    def search(self, q: Optional[str] = None, industry: Optional[str] = None, location: Optional[str] = None,
               status: Optional[str] = None, skip: int = 0, limit: int = 20) -> Tuple[List[Company], int]:
        query = self.db.query(Company)
        if q:
            query = query.filter(Company.name.ilike(f"%{q}%"))
        if industry:
            query = query.filter(func.lower(Company.industry) == industry.lower())
        if location:
            query = query.filter(Company.location.ilike(f"%{location}%"))
        if status:
            query = query.filter(Company.status == status)
        total = query.count()
        return query.order_by(Company.name).offset(skip).limit(limit).all(), total

    def active_job_counts(self, company_ids: Iterable[int]) -> Dict[int, int]:
        ids = list(company_ids)
        if not ids:
            return {}
        rows = (self.db.query(Job.company_id, func.count(Job.id))
                .filter(Job.company_id.in_(ids), Job.status == "ACTIVE").group_by(Job.company_id).all())
        return {cid: n for cid, n in rows}

    def total_jobs(self, company_id: int) -> int:
        return self.db.query(Job).filter(Job.company_id == company_id).count()
