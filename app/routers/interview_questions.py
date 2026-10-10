"""OWNER: M3
Question bank (admin CRUD, everyone can read) + user's personal interview memory bank (/mine).

NOTE: the /mine routes are declared BEFORE /{question_id} so "mine" is not parsed as an id.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.schemas.interview_question import (InterviewQuestionCreate, InterviewQuestionOut,
                                            InterviewQuestionUpdate, QuestionPage)
from app.schemas.user_interview_question import (UserQuestionCreate, UserQuestionOut, UserQuestionPage,
                                                 UserQuestionUpdate)
from app.services.question_service import QuestionService

router = APIRouter(prefix="/interview-questions", tags=["interview-questions"])


@router.get("/ping")
def ping():
    return {"module": "interview_questions", "status": "ok"}


# ------------------------------------------------------------------ my personal questions
@router.post("/mine", response_model=UserQuestionOut, status_code=status.HTTP_201_CREATED)
def add_my_question(data: UserQuestionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return QuestionService(db).create_user_question(user.id, data)


@router.get("/mine", response_model=UserQuestionPage)
def list_my_questions(application_id: Optional[int] = None, asked_by: Optional[str] = None,
                      round: Optional[str] = None, category: Optional[str] = None,
                      skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                      db: Session = Depends(get_db), user=Depends(get_current_user)):
    items, total = QuestionService(db).list_user_questions(
        user.id, application_id=application_id, asked_by=asked_by, round=round, category=category,
        skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.put("/mine/{question_id}", response_model=UserQuestionOut)
def update_my_question(question_id: int, data: UserQuestionUpdate, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    return QuestionService(db).update_user_question(user.id, question_id, data)


@router.delete("/mine/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_question(question_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    QuestionService(db).delete_user_question(user.id, question_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ question bank
@router.post("", response_model=InterviewQuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(data: InterviewQuestionCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return QuestionService(db).create(data, admin)


@router.get("", response_model=QuestionPage)
def list_questions(company_id: Optional[int] = None, job_id: Optional[int] = None,
                   skill_id: Optional[int] = None, category: Optional[str] = None,
                   difficulty: Optional[str] = None, round: Optional[str] = None,
                   experience_level: Optional[str] = None, q: Optional[str] = Query(None, description="search text"),
                   skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    items, total = QuestionService(db).search(
        company_id=company_id, job_id=job_id, skill_id=skill_id, category=category, difficulty=difficulty,
        round=round, experience_level=experience_level, q=q, skip=skip, limit=limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{question_id}", response_model=InterviewQuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return QuestionService(db).get(question_id)


@router.put("/{question_id}", response_model=InterviewQuestionOut)
def update_question(question_id: int, data: InterviewQuestionUpdate, db: Session = Depends(get_db),
                    admin=Depends(require_admin)):
    return QuestionService(db).update(question_id, data)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    QuestionService(db).delete(question_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
