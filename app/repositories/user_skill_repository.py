"""OWNER: M3 - user skill profile and resume match history.

Wraps the M3 tables used by recommendations, skill gap, prep plan, and resume match.
"""
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.resume_match import ResumeMatch
from app.models.user_skill import UserSkill


class UserSkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def skill_ids(self, user_id: int) -> List[int]:
        return [row[0] for row in self.db.query(UserSkill.skill_id)
                .filter(UserSkill.user_id == user_id).all()]

    def replace(self, user_id: int, skill_ids: Iterable[int]) -> None:
        ids = list(dict.fromkeys(int(s) for s in skill_ids if s is not None))
        self.db.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
        for skill_id in ids:
            self.db.add(UserSkill(user_id=user_id, skill_id=skill_id))
        self.db.commit()

    def add_match(self, *, user_id: int, job_id: Optional[int], application_id: Optional[int],
                  resume_filename: Optional[str], match_percent: int,
                  matched: Optional[list], missing: Optional[list]) -> ResumeMatch:
        row = ResumeMatch(
            user_id=user_id,
            job_id=job_id,
            application_id=application_id,
            resume_filename=resume_filename,
            match_percent=match_percent,
            matched=matched,
            missing=missing,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def match_history(self, user_id: int, limit: int = 20) -> List[ResumeMatch]:
        return (self.db.query(ResumeMatch)
                .filter(ResumeMatch.user_id == user_id)
                .order_by(ResumeMatch.id.desc())
                .limit(limit)
                .all())
