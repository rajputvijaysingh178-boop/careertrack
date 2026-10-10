"""OWNER: M3
Responsibility: Skill gap = job skills vs the user's own skill profile (user_skills).
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.matching import match_skills
from app.ai.skill_extractor import topics_for
from app.repositories.prep_lookup_repository import PrepLookupRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.services.prep_target import resolve_target


class SkillGapService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)
        self.profile = UserSkillRepository(db)

    def gap(self, user, job_id: Optional[int] = None, application_id: Optional[int] = None) -> dict:
        target = resolve_target(self.db, user, job_id, application_id)
        mine = self.lookup.skill_names_by_ids(self.profile.skill_ids(user.id))
        result = match_skills(target["skills"], mine)
        result["study_next"] = [{"skill": m["name"], "importance": m["importance"], "topics": topics_for(m["name"])}
                                for m in result["missing"]]
        result["my_skills"] = mine
        if not mine:
            result["note"] = "Your skill profile is empty. Add skills with PUT /recommendations/my-skills."
        result["job"] = ({"id": target["job"]["id"], "title": target["job"].get("title"),
                          "company": target["job"].get("company_name")} if target["job"] else None)
        return result
