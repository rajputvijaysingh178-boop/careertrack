"""OWNER: M1 - DB access for skills"""
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.skill import JobSkill, Skill


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, skill_id: int) -> Optional[Skill]:
        return self.db.get(Skill, skill_id)

    def get_by_name(self, name: str) -> Optional[Skill]:
        return self.db.query(Skill).filter(func.lower(Skill.name) == name.strip().lower()).first()

    def add(self, obj: Skill) -> Skill:
        """Adds and flushes (no commit) so a caller can create skills inside a bigger transaction."""
        self.db.add(obj)
        self.db.flush()
        return obj

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def delete(self, obj: Skill) -> None:
        self.db.delete(obj)
        self.db.commit()

    def search(self, q: Optional[str] = None, category: Optional[str] = None, skip: int = 0,
               limit: int = 100) -> Tuple[List[Skill], int]:
        query = self.db.query(Skill)
        if q:
            query = query.filter(Skill.name.ilike(f"%{q}%"))
        if category:
            query = query.filter(func.lower(Skill.category) == category.lower())
        total = query.count()
        return query.order_by(Skill.name).offset(skip).limit(limit).all(), total

    def categories(self) -> List[str]:
        return [c for (c,) in self.db.query(Skill.category).filter(Skill.category.isnot(None))
                .distinct().order_by(Skill.category).all()]

    def usage_count(self, skill_id: int) -> int:
        return self.db.query(JobSkill).filter(JobSkill.skill_id == skill_id).count()
