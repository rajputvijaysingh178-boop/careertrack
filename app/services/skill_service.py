"""OWNER: M1
Responsibility: the master skills list (everyone, including M2/M3, uses this table).
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.skill import Skill
from app.repositories.skill_repository import SkillRepository
from app.schemas.skill import SkillBulk, SkillCreate, SkillUpdate


class SkillService:
    def __init__(self, db: Session):
        self.repo = SkillRepository(db)

    def list(self, q: Optional[str], category: Optional[str], skip: int, limit: int):
        return self.repo.search(q, category, skip, limit)

    def categories(self) -> list:
        return self.repo.categories()

    def create(self, data: SkillCreate) -> Skill:
        if self.repo.get_by_name(data.name):
            raise DuplicateError("This skill already exists")
        skill = self.repo.add(Skill(name=data.name.strip(), category=data.category))
        self.repo.commit()
        self.repo.refresh(skill)
        return skill

    def bulk_create(self, data: SkillBulk) -> dict:
        created, skipped = [], []
        for item in data.skills:
            if self.repo.get_by_name(item.name):
                skipped.append(item.name)
            else:
                self.repo.add(Skill(name=item.name.strip(), category=item.category))
                created.append(item.name.strip())
        self.repo.commit()
        return {"created": created, "skipped": skipped}

    def update(self, skill_id: int, data: SkillUpdate) -> Skill:
        skill = self.repo.get(skill_id)
        if not skill:
            raise NotFoundError("Skill")
        fields = data.model_dump(exclude_unset=True)
        if fields.get("name") is None:
            fields.pop("name", None)
        if "name" in fields:
            other = self.repo.get_by_name(fields["name"])
            if other and other.id != skill.id:
                raise DuplicateError("This skill already exists")
        for key, value in fields.items():
            setattr(skill, key, value)
        self.repo.commit()
        self.repo.refresh(skill)
        return skill

    def delete(self, skill_id: int) -> None:
        skill = self.repo.get(skill_id)
        if not skill:
            raise NotFoundError("Skill")
        n = self.repo.usage_count(skill_id)
        if n:
            raise HTTPException(409, f"This skill is used by {n} job(s) and cannot be deleted")
        self.repo.delete(skill)
