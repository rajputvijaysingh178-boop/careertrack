"""OWNER: M3
Responsibility: rule-based recommendations (tags / skills matching).
  - user skill profile (user_skills)
  - recommended jobs for the user's skills
  - related content counts for a job (materials, questions, blogs)
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.matching import match_skills
from app.ai.skill_extractor import canonical_key
from app.repositories.prep_lookup_repository import PrepLookupRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.services.prep_workspace_service import PrepWorkspaceService


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)
        self.profile = UserSkillRepository(db)

    # ---------------------------------------------------------------- user skill profile
    def my_skills(self, user_id: int) -> list:
        return self.lookup.skill_names_by_ids(self.profile.skill_ids(user_id))

    def set_my_skills(self, user_id: int, names: list) -> dict:
        catalog_rows = self.lookup.list_skills()
        submitted_names = [raw for raw in names if raw and raw.strip()]
        if submitted_names and not catalog_rows:
            # The lookup repository intentionally degrades query failures to empty
            # lists for optional prep content. A profile write must not interpret a
            # failed/empty catalog lookup as permission to erase a user's skills.
            raise HTTPException(
                status_code=503,
                detail="The skill catalog is empty or unavailable; no profile changes were made. "
                       "Check the skill catalog and server logs, then try again.",
            )
        table = {canonical_key(r["name"]): r for r in catalog_rows if r.get("name")}
        ids, saved, unknown = [], [], []
        for raw in names:
            row = table.get(canonical_key(raw))
            if row:
                if row["id"] not in ids:
                    ids.append(row["id"])
                    saved.append(row["name"])
            elif raw and raw.strip():
                unknown.append(raw.strip())
        # Do not erase a working profile when every submitted name is unknown.
        # This can happen when the browser's skill catalog is stale or the user
        # types a skill that an admin has not added yet. An explicit empty list
        # still clears the profile, preserving the replace semantics.
        if submitted_names and not ids:
            return {"skills": self.my_skills(user_id), "unknown": unknown}

        self.profile.replace(user_id, ids)
        return {"skills": saved, "unknown": unknown}      # unknown = not in the skills table (ask admin to add)

    # ---------------------------------------------------------------- recommended jobs
    def recommend_jobs(self, user_id: int, limit: int = 10) -> dict:
        mine = self.my_skills(user_id)
        available_jobs = self.lookup.active_jobs()
        if not available_jobs:
            note = "No active or unexpired jobs are available yet."
            if not mine:
                note += " No supported skills are saved; add skills from the catalog after jobs are available."
            return {"skills": mine, "jobs": [], "note": note}
        if not mine:
            return {"skills": [], "jobs": [], "note": "Add your skills first (PUT /recommendations/my-skills)."}
        excluded = self.lookup.excluded_job_ids(user_id)
        jobs = [j for j in available_jobs if j["id"] not in excluded]
        skills_map = self.lookup.skills_for_jobs([j["id"] for j in jobs])
        companies = self.lookup.company_names({j["company_id"] for j in jobs if j.get("company_id")})

        results = []
        for j in jobs:
            job_skills = skills_map.get(j["id"])
            if not job_skills:
                continue
            m = match_skills(job_skills, mine)
            if m["match_percent"] > 0:
                results.append({"job_id": j["id"], "title": j.get("title"),
                                "company": companies.get(j.get("company_id")),
                                "match_percent": m["match_percent"], "label": m["label"],
                                "matched": [x["name"] for x in m["matched"]],
                                "missing": [x["name"] for x in m["missing"]]})
        results.sort(key=lambda r: (-r["match_percent"], r["job_id"]))
        payload = {"skills": mine, "jobs": results[:limit]}
        if not results:
            payload["note"] = (
                "No new matching jobs found. Recommendations exclude jobs you have already applied to "
                "or ignored, and only jobs with linked skills can be matched."
            )
        return payload

    # ---------------------------------------------------------------- related content for a job
    def content_for_job(self, job_id: int, user=None) -> dict:
        ws = PrepWorkspaceService(self.db).build_workspace(job_id=job_id, user=user)
        return {"job": ws["job"], "counts": ws["counts"],
                "materials": ws["materials"][:5], "blogs": ws["blogs"][:5]}
