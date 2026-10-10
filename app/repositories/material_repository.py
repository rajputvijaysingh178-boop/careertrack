"""OWNER: M1 - DB access for study materials and material bookmarks"""
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialBookmark


class MaterialRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, material_id: int) -> Optional[Material]:
        return self.db.get(Material, material_id)

    def add(self, obj: Material) -> Material:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj) -> None:
        self.db.refresh(obj)

    def delete(self, obj: Material) -> None:
        self.db.query(MaterialBookmark).filter(MaterialBookmark.material_id == obj.id).delete()
        self.db.delete(obj)
        self.db.commit()

    def search(self, *, q=None, type_=None, skill_id=None, job_id=None, company_id=None, role=None,
               interview_round=None, skip=0, limit=20) -> Tuple[List[Material], int]:
        M = Material
        query = self.db.query(M)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(M.title.ilike(like), M.description.ilike(like)))
        if type_:
            query = query.filter(M.type == type_)
        if skill_id is not None:
            query = query.filter(M.skill_id == skill_id)
        if job_id is not None:
            query = query.filter(M.job_id == job_id)
        if company_id is not None:
            query = query.filter(M.company_id == company_id)
        if role:
            query = query.filter(func.lower(M.role) == role.lower())
        if interview_round:
            query = query.filter(func.lower(M.interview_round) == interview_round.lower())
        total = query.count()
        return query.order_by(M.id.desc()).offset(skip).limit(limit).all(), total

    def for_job(self, job_id: int, company_id: Optional[int], skill_ids: Iterable[int]) -> List[Material]:
        """Materials attached to the job itself, to its company, or to any of its skills."""
        conds = [Material.job_id == job_id]
        if company_id:
            conds.append(Material.company_id == company_id)
        skill_ids = list(skill_ids)
        if skill_ids:
            conds.append(Material.skill_id.in_(skill_ids))
        return self.db.query(Material).filter(or_(*conds)).order_by(Material.id.desc()).all()

    # ---------------------------------------------------------------- bookmarks
    def get_bookmark(self, user_id: int, material_id: int) -> Optional[MaterialBookmark]:
        return (self.db.query(MaterialBookmark)
                .filter(MaterialBookmark.user_id == user_id, MaterialBookmark.material_id == material_id).first())

    def add_bookmark(self, user_id: int, material_id: int) -> None:
        if not self.get_bookmark(user_id, material_id):
            self.db.add(MaterialBookmark(user_id=user_id, material_id=material_id))
            self.db.commit()

    def remove_bookmark(self, obj: MaterialBookmark) -> None:
        self.db.delete(obj)
        self.db.commit()

    def bookmarked(self, user_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[Material], int]:
        query = (self.db.query(Material).join(MaterialBookmark, MaterialBookmark.material_id == Material.id)
                 .filter(MaterialBookmark.user_id == user_id))
        total = query.count()
        return query.order_by(MaterialBookmark.id.desc()).offset(skip).limit(limit).all(), total

    def bookmarked_ids(self, user_id: int, material_ids: Iterable[int]) -> set:
        ids = list(material_ids)
        if not ids:
            return set()
        rows = (self.db.query(MaterialBookmark.material_id)
                .filter(MaterialBookmark.user_id == user_id, MaterialBookmark.material_id.in_(ids)).all())
        return {r[0] for r in rows}
