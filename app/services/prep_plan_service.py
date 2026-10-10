"""OWNER: M3
Responsibility: "Prepare Me for This Job" -> N-day plan (rule-based, optional AI), enriched with questions
from the question bank.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMUnavailable, complete_json
from app.ai.plan_builder import build_plan
from app.ai.prompts import SYSTEM_JSON, prep_plan_prompt
from app.repositories.prep_lookup_repository import PrepLookupRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.user_skill_repository import UserSkillRepository
from app.services.prep_target import resolve_target


class PrepPlanService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)
        self.questions = QuestionRepository(db)
        self.profile = UserSkillRepository(db)

    def generate(self, user, *, job_id: Optional[int] = None, application_id: Optional[int] = None,
                 jd_text: Optional[str] = None, days: int = 7, use_ai: bool = False) -> dict:
        target = resolve_target(self.db, user, job_id, application_id, jd_text)
        skills = target["skills"]
        known = self.lookup.skill_names_by_ids(self.profile.skill_ids(user.id))

        plan, source, ai_error = None, "rules", None
        if use_ai and skills:
            try:
                plan = self._ai_plan(skills, days, target["role_title"])
                source = "ai"
            except LLMUnavailable as exc:
                ai_error = str(exc)
        if plan is None:
            plan = build_plan(skills, days, known)
        self._attach_questions(plan, target, skills)

        out = {"role": target["role_title"], "days": len(plan), "source": source, "skills": skills, "plan": plan}
        if ai_error:
            out["ai_error"] = ai_error
        return out

    # ------------------------------------------------------------------
    @staticmethod
    def _ai_plan(skills: list, days: int, role: Optional[str]) -> list:
        data = complete_json(prep_plan_prompt([s["name"] for s in skills], days, role or ""), SYSTEM_JSON)
        raw = data.get("days")
        if not isinstance(raw, list) or not raw:
            raise LLMUnavailable("AI plan had no days")
        plan = []
        for i, d in enumerate(raw[:30], start=1):
            if not isinstance(d, dict) or not isinstance(d.get("title"), str):
                raise LLMUnavailable("AI plan had an invalid day")
            plan.append({"day": i, "title": d["title"], "skills": [],
                         "topics": [str(t) for t in d.get("topics", []) if isinstance(t, (str, int))],
                         "tasks": [str(t) for t in d.get("tasks", []) if isinstance(t, (str, int))]})
        return plan

    def _attach_questions(self, plan: list, target: dict, skills: list) -> None:
        names = [s["name"] for s in skills]
        rows = self.lookup.skills_by_names(names)
        id_to_name = {r["id"]: r["name"].lower() for r in rows.values()}
        pool = self.questions.for_targets(target["job_id"], target["company_id"], id_to_name.keys(), names)
        for day in plan:
            wanted = {n.lower() for n in day.get("skills", [])}
            picks = []
            for q in pool:
                if (q.category or "").lower() in wanted or id_to_name.get(q.skill_id) in wanted:
                    picks.append({"id": q.id, "question": q.question, "difficulty": q.difficulty})
                if len(picks) == 5:
                    break
            day["questions"] = picks
