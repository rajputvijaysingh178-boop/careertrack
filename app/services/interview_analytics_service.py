"""OWNER: M3
Responsibility: interview analytics built from the user's personal question memory + resume match history.
"""
from collections import Counter

from sqlalchemy.orm import Session

from app.repositories.question_repository import QuestionRepository
from app.repositories.user_skill_repository import UserSkillRepository


def _counts(values) -> dict:
    return dict(Counter(v for v in values if v).most_common())


class InterviewAnalyticsService:
    def __init__(self, db: Session):
        self.questions = QuestionRepository(db)
        self.matches = UserSkillRepository(db)

    def analytics(self, user_id: int) -> dict:
        items = self.questions.all_user_questions(user_id)
        weak = [q for q in items if (q.need_to_improve or "").strip()]
        unanswered = [q for q in items if not (q.my_answer or "").strip()]
        history = self.matches.match_history(user_id, 50)
        avg = round(sum(h.match_percent or 0 for h in history) / len(history)) if history else None
        return {
            "total_questions": len(items),
            "by_company": _counts(q.asked_by for q in items),
            "by_round": _counts(q.round for q in items),
            "by_difficulty": _counts(q.difficulty for q in items),
            "by_category": _counts(q.category for q in items),
            "need_to_improve_count": len(weak),
            "unanswered_count": len(unanswered),
            "focus_areas": [{"id": q.id, "question": q.question, "need_to_improve": q.need_to_improve}
                            for q in sorted(weak, key=lambda x: -x.id)[:10]],
            "resume_matches": {"count": len(history), "average_percent": avg},
        }
