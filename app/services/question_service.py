"""OWNER: M3
Responsibility: question bank (admin) + user's personal interview memory bank.
Business rules live here; DB access is in QuestionRepository.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.repositories.question_repository import QuestionRepository
from app.schemas.interview_question import InterviewQuestionCreate, InterviewQuestionUpdate
from app.schemas.user_interview_question import UserQuestionCreate, UserQuestionUpdate

_NOT_NULLABLE = ("category", "question", "difficulty")


class QuestionService:
    def __init__(self, db: Session):
        self.repo = QuestionRepository(db)

    # ---------------------------------------------------------------- admin question bank
    def create(self, data: InterviewQuestionCreate, user):
        return self.repo.create(**data.model_dump(), created_by=user.id)

    def get(self, question_id: int):
        obj = self.repo.get(question_id)
        if not obj:
            raise NotFoundError("Question")
        return obj

    def update(self, question_id: int, data: InterviewQuestionUpdate):
        obj = self.get(question_id)
        fields = data.model_dump(exclude_unset=True)
        for key in _NOT_NULLABLE:                       # these columns can't be set to null
            if key in fields and fields[key] is None:
                fields.pop(key)
        return self.repo.update(obj, **fields)

    def delete(self, question_id: int) -> None:
        self.repo.delete(self.get(question_id))

    def search(self, **filters):
        return self.repo.search(**filters)

    # ---------------------------------------------------------------- user's personal questions
    def create_user_question(self, user_id: int, data: UserQuestionCreate):
        if data.application_id is not None and not self.repo.application_owned(user_id, data.application_id):
            raise NotFoundError("Application")
        return self.repo.create_user_question(user_id=user_id, **data.model_dump())

    def get_user_question(self, user_id: int, question_id: int):
        obj = self.repo.get_user_question(user_id, question_id)   # filtered by user -> others get 404
        if not obj:
            raise NotFoundError("Question")
        return obj

    def update_user_question(self, user_id: int, question_id: int, data: UserQuestionUpdate):
        obj = self.get_user_question(user_id, question_id)
        fields = data.model_dump(exclude_unset=True)
        if fields.get("application_id") is not None and not self.repo.application_owned(
            user_id, fields["application_id"]
        ):
            raise NotFoundError("Application")
        if fields.get("question") is None:
            fields.pop("question", None)
        return self.repo.update(obj, **fields)

    def delete_user_question(self, user_id: int, question_id: int) -> None:
        self.repo.delete(self.get_user_question(user_id, question_id))

    def list_user_questions(self, user_id: int, **filters):
        return self.repo.list_user_questions(user_id, **filters)
