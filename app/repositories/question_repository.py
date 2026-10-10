"""OWNER: M3 - DB access for interview_questions and user_interview_questions (no business rules)."""
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.interview_question import InterviewQuestion
from app.models.user_interview_question import UserInterviewQuestion


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------ admin question bank
    def get(self, question_id: int) -> Optional[InterviewQuestion]:
        return self.db.get(InterviewQuestion, question_id)

    def create(self, **fields) -> InterviewQuestion:
        obj = InterviewQuestion(**fields)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: InterviewQuestion, **fields) -> InterviewQuestion:
        for k, v in fields.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj) -> None:
        self.db.delete(obj)
        self.db.commit()

    def search(self, *, company_id=None, job_id=None, skill_id=None, category=None, difficulty=None,
               round=None, experience_level=None, q=None, skip=0, limit=20) -> Tuple[List[InterviewQuestion], int]:
        Q = InterviewQuestion
        query = self.db.query(Q)
        if company_id is not None:
            query = query.filter(Q.company_id == company_id)
        if job_id is not None:
            query = query.filter(Q.job_id == job_id)
        if skill_id is not None:
            query = query.filter(Q.skill_id == skill_id)
        if category:
            query = query.filter(func.lower(Q.category) == category.lower())
        if difficulty:
            query = query.filter(Q.difficulty == difficulty.upper())
        if round:
            query = query.filter(func.lower(Q.round) == round.lower())
        if experience_level:
            query = query.filter(func.lower(Q.experience_level) == experience_level.lower())
        if q:
            query = query.filter(Q.question.ilike(f"%{q}%"))
        total = query.count()
        items = query.order_by(Q.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def for_targets(self, job_id: Optional[int] = None, company_id: Optional[int] = None,
                    skill_ids: Optional[Iterable[int]] = None, categories: Optional[Iterable[str]] = None,
                    limit: int = 300) -> List[InterviewQuestion]:
        """Questions linked to ANY of: this job, this company, these skills, these categories."""
        Q = InterviewQuestion
        conds = []
        if job_id:
            conds.append(Q.job_id == job_id)
        if company_id:
            conds.append(Q.company_id == company_id)
        skill_ids = list(skill_ids or [])
        if skill_ids:
            conds.append(Q.skill_id.in_(skill_ids))
        cats = [c.lower() for c in (categories or [])]
        if cats:
            conds.append(func.lower(Q.category).in_(cats))
        if not conds:
            return []
        return self.db.query(Q).filter(or_(*conds)).limit(limit).all()

    # ------------------------------------------------ user's personal questions
    def get_user_question(self, user_id: int, question_id: int) -> Optional[UserInterviewQuestion]:
        U = UserInterviewQuestion
        return self.db.query(U).filter(U.id == question_id, U.user_id == user_id).first()

    def create_user_question(self, **fields) -> UserInterviewQuestion:
        obj = UserInterviewQuestion(**fields)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_user_questions(self, user_id: int, *, application_id=None, asked_by=None, round=None,
                            category=None, skip=0, limit=50) -> Tuple[List[UserInterviewQuestion], int]:
        U = UserInterviewQuestion
        query = self.db.query(U).filter(U.user_id == user_id)
        if application_id is not None:
            query = query.filter(U.application_id == application_id)
        if asked_by:
            query = query.filter(func.lower(U.asked_by) == asked_by.lower())
        if round:
            query = query.filter(func.lower(U.round) == round.lower())
        if category:
            query = query.filter(func.lower(U.category) == category.lower())
        total = query.count()
        items = query.order_by(U.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def all_user_questions(self, user_id: int) -> List[UserInterviewQuestion]:
        U = UserInterviewQuestion
        return self.db.query(U).filter(U.user_id == user_id).all()
