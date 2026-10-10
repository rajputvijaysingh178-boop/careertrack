from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.exceptions import InvalidTransitionError, NotFoundError
from app.models.company import Company
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.schemas.application_event import ApplicationEventCreate, HRCallCreate
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.schemas.note import NoteCreate
from app.schemas.reminder import ReminderCreate
from app.schemas.user_interview_question import UserQuestionCreate, UserQuestionUpdate
from app.services.analytics_service import AnalyticsService
from app.services.application_service import ApplicationService
from app.services.interview_service import InterviewService
from app.services.notes_service import NotesService
from app.services.reminder_service import ReminderService
from app.services.question_service import QuestionService
from app.core.time import utcnow


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def users(db):
    first = User(name="One", email="one@example.test", password_hash="hash")
    second = User(name="Two", email="two@example.test", password_hash="hash")
    db.add_all([first, second])
    db.commit()
    return first, second


def test_application_snapshots_job_and_enforces_owner_and_transition(db, users):
    owner, other = users
    company = Company(name="Example Co")
    db.add(company)
    db.flush()
    job = Job(company_id=company.id, title="Backend Engineer", description="Python and APIs",
              status="ACTIVE", location="Remote")
    db.add(job)
    db.commit()

    service = ApplicationService(db)
    app = service.create(owner.id, ApplicationCreate(job_id=job.id))
    assert app.job_title == "Backend Engineer"
    assert app.company_name == "Example Co"
    assert app.jd_text == "Python and APIs"
    with pytest.raises(NotFoundError):
        service.get(app.id, other.id)
    with pytest.raises(InvalidTransitionError):
        service.change_status(app.id, owner.id, "ACCEPTED")

    service.change_status(app.id, owner.id, "APPLIED", "Submitted online")
    history = service.history(app.id, owner.id)
    assert [(row.old_status, row.new_status) for row in history] == [(None, "SAVED"), ("SAVED", "APPLIED")]
    assert history[-1].comment == "Submitted online"


def test_interview_rounds_and_status_history_are_application_scoped(db, users):
    owner, other = users
    service = ApplicationService(db)
    app = service.create(owner.id, ApplicationCreate(job_title="Data Analyst", status="APPLIED"))
    interviews = InterviewService(db)
    round_one = interviews.create(app.id, owner.id, InterviewCreate(
        round_name="Technical Round 1", scheduled_at=datetime(2026, 10, 15, 9, 0),
        mode="VIDEO", interviewer="Alex", feedback="Strong SQL"))
    interviews.update(round_one.id, owner.id, InterviewUpdate(
        scheduled_at=datetime(2026, 10, 16, 9, 0), interviewer="Alex Chen", feedback="Strong SQL"))
    interviews.update(round_one.id, owner.id, InterviewUpdate(status="COMPLETED", feedback="Strong SQL; move forward"))

    rows = interviews.list_for_application(app.id, owner.id)
    assert len(rows) == 1
    assert rows[0].application_id == app.id
    assert rows[0].round_name == "Technical Round 1"
    assert rows[0].feedback == "Strong SQL; move forward"
    history = interviews.history(round_one.id, owner.id)
    assert [(h.old_status, h.new_status) for h in history] == [
        (None, "SCHEDULED"), ("SCHEDULED", "SCHEDULED"), ("SCHEDULED", "COMPLETED")
    ]
    assert history[1].round_name == "Technical Round 1"
    assert history[1].scheduled_at == datetime(2026, 10, 16, 9, 0)
    assert history[1].interviewer == "Alex Chen"
    assert history[1].feedback == "Strong SQL"
    assert history[-1].feedback == "Strong SQL; move forward"
    with pytest.raises(NotFoundError):
        interviews.list_for_application(app.id, other.id)


def test_partial_application_update_keeps_other_values(db, users):
    owner, _ = users
    service = ApplicationService(db)
    app = service.create(owner.id, ApplicationCreate(job_title="QA Engineer", source="Referral"))
    updated = service.update(app.id, owner.id, ApplicationUpdate(location="Pune"))
    assert updated.source == "Referral"
    assert updated.location == "Pune"


def test_hr_calls_and_manual_timeline_events_are_application_scoped(db, users):
    owner, other = users
    service = ApplicationService(db)
    app = service.create(owner.id, ApplicationCreate(job_title="Product Engineer", company_name="Example Co"))
    call = service.add_hr_call(app.id, owner.id, HRCallCreate(
        hr_name="Priya", discussion="Discussed schedule", next_round="Technical", notes="Review APIs"))
    event = service.add_event(app.id, owner.id, ApplicationEventCreate(
        title="Resume sent", details="Sent revised PDF"))
    assert service.hr_calls(app.id, owner.id) == [call]
    assert call.company_name == "Example Co"
    assert service.events(app.id, owner.id) == [event]
    with pytest.raises(NotFoundError):
        service.add_hr_call(app.id, other.id, HRCallCreate(hr_name="Not authorized"))
    with pytest.raises(NotFoundError):
        service.add_event(app.id, other.id, ApplicationEventCreate(title="Not authorized"))


def test_analytics_uses_status_history_and_notes_reminders_are_private(db, users, monkeypatch):
    owner, other = users
    owner_id = owner.id
    applications = ApplicationService(db)
    app = applications.create(owner.id, ApplicationCreate(job_title="Security Engineer", status="APPLIED",
                                                           source="Referral"))
    for status in ("HR_CONTACTED", "INTERVIEW_SCHEDULED", "INTERVIEW_1", "HR_ROUND", "OFFER_RECEIVED"):
        applications.change_status(app.id, owner.id, status)
    InterviewService(db).create(app.id, owner.id, InterviewCreate(
        round_name="Final round", scheduled_at=utcnow() + timedelta(days=2)))
    metrics = AnalyticsService(db).summary(owner.id)
    assert metrics["response_rate"] == 100.0
    assert metrics["interview_rate"] == 100.0
    assert metrics["offer_rate"] == 100.0
    assert metrics["response_to_interview_rate"] == 100.0
    assert metrics["interview_to_offer_rate"] == 100.0
    assert metrics["by_source_response_rate"] == {"Referral": 100.0}
    assert len(metrics["upcoming_interviews"]) == 1
    assert metrics["upcoming_interviews"][0]["application_id"] == app.id
    notes = NotesService(db)
    note = notes.create(owner.id, NoteCreate(application_id=app.id, title="Recruiter", content="Send portfolio"))
    assert notes.list(owner.id, app.id) == [note]
    with pytest.raises(NotFoundError):
        notes.list(other.id, app.id)
    reminders = ReminderService(db)
    reminder = reminders.create(owner.id, ReminderCreate(application_id=app.id, title="Follow up",
                                                          reminder_time=datetime(2000, 1, 1, 12, 0)))
    assert reminders.list(owner_id) == [reminder]
    assert reminders.list(other.id) == []
    from app.tasks import send_reminders
    monkeypatch.setattr(send_reminders, "SessionLocal", lambda: db)
    assert send_reminders.send_due_reminders() == 1
    assert reminders.list(owner_id)[0].status == "DUE"


def test_interview_memory_can_only_link_to_owners_application(db, users):
    owner, other = users
    applications = ApplicationService(db)
    own_app = applications.create(owner.id, ApplicationCreate(job_title="Backend Engineer"))
    other_app = applications.create(other.id, ApplicationCreate(job_title="Product Engineer"))
    questions = QuestionService(db)

    item = questions.create_user_question(owner.id, UserQuestionCreate(
        question="How do you design a reliable API?", application_id=own_app.id
    ))
    assert item.application_id == own_app.id
    with pytest.raises(NotFoundError):
        questions.create_user_question(owner.id, UserQuestionCreate(
            question="How do you design a reliable API?", application_id=other_app.id
        ))
    with pytest.raises(NotFoundError):
        questions.update_user_question(owner.id, item.id, UserQuestionUpdate(application_id=other_app.id))
    assert questions.list_user_questions(owner.id, application_id=own_app.id)[0][0].id == item.id
