"""OWNER: M1
Responsibility: company CRUD. One company has many jobs.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import is_admin
from app.core.exceptions import DuplicateError, NotFoundError
from app.models.company import Company
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate


class CompanyService:
    def __init__(self, db: Session):
        self.repo = CompanyRepository(db)

    def _out(self, companies: list) -> list:
        counts = self.repo.active_job_counts([c.id for c in companies])
        result = []
        for c in companies:
            item = CompanyOut.model_validate(c)
            item.active_jobs = counts.get(c.id, 0)
            result.append(item)
        return result

    def create(self, data: CompanyCreate) -> CompanyOut:
        if self.repo.get_by_name(data.name):
            raise DuplicateError("A company with this name already exists")
        company = self.repo.add(Company(**data.model_dump(), status="ACTIVE"))
        return self._out([company])[0]

    def get(self, company_id: int, user=None) -> CompanyOut:
        company = self.repo.get(company_id)
        if not company or (company.status != "ACTIVE" and not is_admin(user)):
            raise NotFoundError("Company")
        return self._out([company])[0]

    def list(self, user, q: Optional[str], industry: Optional[str], location: Optional[str],
             status: Optional[str], skip: int, limit: int) -> dict:
        admin = is_admin(user)
        items, total = self.repo.search(q, industry, location, status.upper() if (admin and status) else
                                        (None if admin else "ACTIVE"), skip, limit)
        return {"items": self._out(items), "total": total, "skip": skip, "limit": limit}

    def update(self, company_id: int, data: CompanyUpdate) -> CompanyOut:
        company = self.repo.get(company_id)
        if not company:
            raise NotFoundError("Company")
        fields = data.model_dump(exclude_unset=True)
        if fields.get("name") is None:
            fields.pop("name", None)
        if fields.get("status") is None:
            fields.pop("status", None)
        if "name" in fields:
            other = self.repo.get_by_name(fields["name"])
            if other and other.id != company.id:
                raise DuplicateError("A company with this name already exists")
        for key, value in fields.items():
            setattr(company, key, value)
        self.repo.commit()
        self.repo.refresh(company)
        return self._out([company])[0]

    def delete(self, company_id: int) -> None:
        company = self.repo.get(company_id)
        if not company:
            raise NotFoundError("Company")
        n = self.repo.total_jobs(company_id)
        if n:
            raise HTTPException(409, f"This company has {n} job(s). Set its status to INACTIVE instead of deleting it.")
        self.repo.delete(company)
