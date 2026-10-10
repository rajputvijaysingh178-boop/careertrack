"""OWNER: M3
Responsibility: Interview Prep Workspace = Job -> Skills -> Questions -> Materials -> Blogs (+ my questions).

M2 integration: M2's  GET /applications/{id}  can call
    PrepWorkspaceService(db).build_workspace(job_id=app.job_id, application_id=app.id, user=user)
and return it as the `prep` block.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.prep_lookup_repository import PrepLookupRepository
from app.repositories.question_repository import QuestionRepository
from app.services.prep_target import resolve_target


def question_to_dict(q) -> dict:
    return {"id": q.id, "category": q.category, "question": q.question, "difficulty": q.difficulty,
            "experience_level": q.experience_level, "round": q.round, "expected_topics": q.expected_topics or [],
            "answer": q.answer, "company_id": q.company_id, "job_id": q.job_id, "skill_id": q.skill_id}


class PrepWorkspaceService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)
        self.questions = QuestionRepository(db)

    def build_workspace(self, job_id: Optional[int] = None, application_id: Optional[int] = None, user=None,
                        jd_text: Optional[str] = None, max_questions: int = 60) -> dict:
        target = resolve_target(self.db, user, job_id, application_id, jd_text)
        skill_names = [s["name"] for s in target["skills"]]
        skill_rows = self.lookup.skills_by_names(skill_names)
        skill_ids = {r["id"] for r in skill_rows.values()}
        cats = {n.lower() for n in skill_names}

        # ---- questions: job > company > skill > category, grouped by category
        found = self.questions.for_targets(target["job_id"], target["company_id"], skill_ids, skill_names)

        def score(q) -> int:
            s = 0
            if target["job_id"] and q.job_id == target["job_id"]:
                s += 4
            if target["company_id"] and q.company_id == target["company_id"]:
                s += 2
            if q.skill_id in skill_ids:
                s += 2
            if (q.category or "").lower() in cats:
                s += 1
            return s

        ranked = sorted(found, key=lambda q: (-score(q), q.id))[:max_questions]
        by_category: dict = {}
        for q in ranked:
            by_category.setdefault(q.category, []).append(question_to_dict(q))

        materials = self.lookup.materials_for(target["job_id"], target["company_id"], skill_ids)
        blogs = self.lookup.blogs_for(skill_names)

        my_questions = []
        if user is not None and application_id is not None:
            items, _ = self.questions.list_user_questions(user.id, application_id=application_id, limit=100)
            my_questions = [{"id": u.id, "question": u.question, "round": u.round, "difficulty": u.difficulty,
                             "my_answer": u.my_answer, "need_to_improve": u.need_to_improve} for u in items]

        job = target["job"]
        return {
            "job": {"id": job["id"], "title": job.get("title"), "company": job.get("company_name")} if job else None,
            "application_id": application_id,
            "skills": target["skills"],
            "questions": {"total": len(ranked), "by_category": by_category},
            "materials": materials,
            "blogs": blogs,
            "my_questions": my_questions,
            "counts": {"questions": len(ranked), "materials": len(materials), "blogs": len(blogs)},
        }
