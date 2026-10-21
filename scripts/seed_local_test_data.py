"""Seed repeatable CareerTrack product data into a dedicated local SQLite DB.

Usage from the backend directory:
    python -m scripts.seed_local_test_data
    python -m scripts.seed_local_test_data --db-path .testdata/careertrack-seed.db

This command never reads DATABASE_URL from .env and refuses non-SQLite or paths
outside the backend's .testdata directory. It creates test schema with SQLAlchemy
metadata; it does not run Alembic migrations.
"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Prevent importing application modules from initializing their global engine
# against a developer's configured database. The seeder creates its own engine.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ.setdefault("SECRET_KEY", "careertrack-local-test-only-secret-not-for-deployment")

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - populate Base.metadata
from app.core.database import Base
from app.core.security import hash_password
from app.models import (
    Application,
    ApplicationEvent,
    ApplicationStatusHistory,
    Blog,
    Bookmark,
    Company,
    Document,
    HRCall,
    Interview,
    InterviewQuestion,
    InterviewStatusHistory,
    Job,
    JobSkill,
    Material,
    Note,
    Reminder,
    ResumeMatch,
    Skill,
    User,
    UserInterviewQuestion,
    UserSkill,
)
from app.models.material import MaterialBookmark


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / ".testdata" / "careertrack-seed.db"

ADMIN_EMAIL = "admin+careertrack-test@example.com"
ADMIN_PASSWORD = "CT-Test-Admin-2026!"
USERS = (
    ("asha.sharma+careertrack-test@example.com", "Asha Sharma", "CT-Test-Asha-2026!", "Hyderabad"),
    ("rohan.mehta+careertrack-test@example.com", "Rohan Mehta", "CT-Test-Rohan-2026!", "Bengaluru"),
)

COMPANY_SPECS = (
    {
        "name": "[TEST] Cognizant",
        "industry": "IT Services",
        "location": "Hyderabad",
        "company_size": "10000+",
        "website": "https://www.cognizant.com/",
        "description": "Test-only Cognizant-style employer profile for QA and applied AI roles.",
    },
    {
        "name": "[TEST] Deloitte",
        "industry": "Consulting",
        "location": "Bengaluru",
        "company_size": "10000+",
        "website": "https://www.deloitte.com/",
        "description": "Test-only Deloitte-style employer profile for software engineering roles.",
    },
)

SKILL_SPECS = (
    ("Python", "Programming"),
    ("Playwright", "Testing"),
    ("Selenium", "Testing"),
    ("API Testing", "Testing"),
    ("GenAI", "Artificial Intelligence"),
    ("LLM", "Artificial Intelligence"),
    ("FastAPI", "Backend"),
    ("PostgreSQL", "Data"),
    ("Docker", "Cloud & DevOps"),
    ("AWS", "Cloud & DevOps"),
)

JOB_SPECS = (
    {
        "key": "qa",
        "company": "[TEST] Cognizant",
        "title": "[TEST] GenAI QA Engineer",
        "location": "Hyderabad",
        "work_mode": "HYBRID",
        "employment_type": "FULL_TIME",
        "job_type": "QA",
        "experience_min": 1,
        "experience_max": 3,
        "salary_min": 6,
        "salary_max": 10,
        "application_url": "https://careers.cognizant.com/test/genai-qa-engineer",
        "required": ("Python", "Playwright", "API Testing", "GenAI"),
        "preferred": ("Selenium", "LLM"),
        "description": (
            "[TEST DATA] GenAI QA Engineer — Hyderabad (Hybrid), full-time, 1–3 years, "
            "₹6–10 LPA. Design and maintain UI and API automation for AI-enabled products.\n\n"
            "Responsibilities: build Playwright and Python test suites; validate REST APIs and "
            "LLM responses; investigate defects with engineering; report coverage and release risks.\n\n"
            "Required: Python, Playwright, API Testing, GenAI. Preferred: Selenium and LLM evaluation."
        ),
    },
    {
        "key": "backend",
        "company": "[TEST] Deloitte",
        "title": "[TEST] Python Backend Developer",
        "location": "Bengaluru",
        "work_mode": "HYBRID",
        "employment_type": "FULL_TIME",
        "job_type": "Backend",
        "experience_min": 2,
        "experience_max": 4,
        "salary_min": 8,
        "salary_max": 14,
        "application_url": "https://careers.deloitte.com/test/python-backend-developer",
        "required": ("Python", "FastAPI", "PostgreSQL", "Docker"),
        "preferred": ("AWS", "API Testing"),
        "description": (
            "[TEST DATA] Python Backend Developer — Bengaluru (Hybrid), full-time, 2–4 years, "
            "₹8–14 LPA. Develop secure APIs and reliable data services for enterprise clients.\n\n"
            "Responsibilities: implement FastAPI endpoints; design PostgreSQL queries; add automated "
            "tests; package services with Docker; collaborate on production support.\n\n"
            "Required: Python, FastAPI, PostgreSQL, Docker. Preferred: AWS and API Testing."
        ),
    },
)

COUNT_MODELS = {
    "companies": Company,
    "jobs": Job,
    "skills": Skill,
    "job_skills": JobSkill,
    "users": User,
    "user_skills": UserSkill,
    "applications": Application,
    "application_status_history": ApplicationStatusHistory,
    "application_events": ApplicationEvent,
    "hr_calls": HRCall,
    "interviews": Interview,
    "interview_status_history": InterviewStatusHistory,
    "notes": Note,
    "reminders": Reminder,
    "bookmarks": Bookmark,
    "documents": Document,
    "interview_questions": InterviewQuestion,
    "user_interview_questions": UserInterviewQuestion,
    "materials": Material,
    "material_bookmarks": MaterialBookmark,
    "blogs": Blog,
    "resume_matches": ResumeMatch,
}


def get_or_create(session: Session, model, lookup: dict, values: dict):
    """Return a stable natural-key record without changing existing user data."""
    record = session.query(model).filter_by(**lookup).one_or_none()
    if record is not None:
        return record, False
    record = model(**{**lookup, **values})
    session.add(record)
    session.flush()
    return record, True


def _ensure_account(session: Session, *, email: str, name: str, password: str,
                    role: str, location: str) -> User:
    user = session.query(User).filter_by(email=email).one_or_none()
    if user:
        if user.role != role:
            raise RuntimeError(f"Test account {email} exists with a different role; refusing to modify it.")
        if user.status != "ACTIVE":
            raise RuntimeError(f"Test account {email} is not ACTIVE; refusing to modify it.")
        return user
    user = User(name=name, email=email, password_hash=hash_password(password), role=role,
                status="ACTIVE", location=location)
    session.add(user)
    session.flush()
    return user


def seed_data(engine: Engine) -> dict[str, int]:
    """Create model-backed sample content and private user workflows in SQLite."""
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Local CareerTrack test data may only be seeded into SQLite.")

    Base.metadata.create_all(bind=engine)
    now = datetime(2026, 10, 21, 9, 0)
    with Session(engine) as session, session.begin():
        admin = _ensure_account(session, email=ADMIN_EMAIL, name="CareerTrack Test Admin",
                                password=ADMIN_PASSWORD, role="ADMIN", location="Hyderabad")
        users = {
            email: _ensure_account(session, email=email, name=name, password=password,
                                   role="USER", location=location)
            for email, name, password, location in USERS
        }

        companies = {}
        for spec in COMPANY_SPECS:
            company, _ = get_or_create(session, Company, {"name": spec["name"]},
                                       {**{k: v for k, v in spec.items() if k != "name"}, "status": "ACTIVE"})
            companies[spec["name"]] = company

        skills = {}
        for name, category in SKILL_SPECS:
            skill, _ = get_or_create(session, Skill, {"name": name}, {"category": category})
            skills[name] = skill

        jobs = {}
        for spec in JOB_SPECS:
            company = companies[spec["company"]]
            job_values = {key: value for key, value in spec.items()
                          if key not in {"key", "company", "required", "preferred"}}
            job_values.update({
                "posted_date": date(2026, 10, 19),
                "expiry_date": date(2027, 1, 31),
                "status": "ACTIVE",
                "created_by": admin.id,
            })
            job, _ = get_or_create(session, Job,
                                   {"company_id": company.id, "title": spec["title"]}, job_values)
            jobs[spec["key"]] = job
            for skill_name in (*spec["required"], *spec["preferred"]):
                importance = "REQUIRED" if skill_name in spec["required"] else "PREFERRED"
                get_or_create(session, JobSkill,
                              {"job_id": job.id, "skill_id": skills[skill_name].id},
                              {"importance": importance})

        for email, user in users.items():
            for skill_name in (("Python", "Playwright") if email.startswith("asha.")
                               else ("Python", "FastAPI")):
                get_or_create(session, UserSkill,
                              {"user_id": user.id, "skill_id": skills[skill_name].id}, {})

        blog_specs = (
            ("[TEST] GenAI QA Engineer Interview Guide", "test-genai-qa-interview-guide",
             "QA", ["Python", "Playwright", "GenAI", "Interview"],
             "A practical guide to preparing Python, Playwright, API Testing and GenAI evaluation examples."),
            ("[TEST] Python API Engineering Preparation Guide", "test-python-api-engineering-guide",
             "Backend", ["Python", "FastAPI", "PostgreSQL", "Interview"],
             "Review FastAPI dependencies, PostgreSQL query design, API validation and Docker deployment."),
        )
        for title, slug, category, tags, content in blog_specs:
            get_or_create(session, Blog, {"slug": slug}, {
                "title": title, "content": content, "category": category, "tags": tags,
                "author_id": admin.id, "status": "PUBLISHED", "published_at": now,
            })

        material_specs = (
            ("[TEST] Playwright Python Getting Started", "https://playwright.dev/python/docs/intro",
             "ARTICLE", "Playwright", "QA", "Technical 1", "qa"),
            ("[TEST] FastAPI Tutorial and API Testing", "https://fastapi.tiangolo.com/tutorial/",
             "ARTICLE", "FastAPI", "Backend", "Technical 1", "backend"),
        )
        materials = {}
        for title, url, kind, skill_name, role, round_name, job_key in material_specs:
            material, _ = get_or_create(session, Material, {"title": title}, {
                "file_url": url, "type": kind, "description": "Public test study material link.",
                "skill_id": skills[skill_name].id, "job_id": jobs[job_key].id,
                "company_id": jobs[job_key].company_id, "role": role,
                "interview_round": round_name, "created_by": admin.id,
            })
            materials[job_key] = material

        question_specs = (
            ("Explain how you would test an LLM-powered API for stable behavior.", "GenAI", "qa",
             "API Testing", ["Test cases", "Prompt variation", "Regression checks"]),
            ("How do FastAPI dependencies help structure authentication and database access?",
             "FastAPI", "backend", "FastAPI", ["Dependency injection", "Request scope", "Testing"]),
        )
        for question, category, job_key, skill_name, topics in question_specs:
            job = jobs[job_key]
            get_or_create(session, InterviewQuestion, {"question": question}, {
                "company_id": job.company_id, "job_id": job.id, "skill_id": skills[skill_name].id,
                "category": category, "difficulty": "MEDIUM", "experience_level": "1-3 Years",
                "round": "Technical 1", "expected_topics": topics,
                "answer": "Describe the approach, trade-offs, and a concrete verification example.",
                "created_by": admin.id,
            })

        app_rows: dict[str, list[Application]] = {email: [] for email in users}
        app_statuses = (
            (USERS[0][0], "qa", "APPLIED", ["APPLIED"]),
            (USERS[0][0], "backend", "INTERVIEW_SCHEDULED",
             ["APPLIED", "HR_CONTACTED", "INTERVIEW_SCHEDULED"]),
            (USERS[1][0], "qa", "APPLICATION_VIEWED", ["APPLIED", "APPLICATION_VIEWED"]),
            (USERS[1][0], "backend", "REJECTED", ["APPLIED", "REJECTED"]),
        )
        for index, (email, job_key, status, history_statuses) in enumerate(app_statuses):
            user = users[email]
            job = jobs[job_key]
            company = companies["[TEST] Cognizant" if job_key == "qa" else "[TEST] Deloitte"]
            application, created = get_or_create(session, Application,
                {"user_id": user.id, "job_id": job.id}, {
                    "company_id": company.id,
                    "applied_date": now - timedelta(days=12 - index),
                    "status": status,
                    "source": "Company Website",
                    "application_url": job.application_url,
                    "resume_version": "CareerTrack-Test-Resume-v1.pdf",
                    "salary_expectation": job.salary_min,
                    "hr_name": "Priya Nair" if job_key == "qa" else "Arjun Rao",
                    "hr_contact": "test-contact@example.invalid",
                    "job_title": job.title,
                    "company_name": company.name,
                    "jd_text": job.description,
                    "skills": ", ".join(spec_skill for spec_skill in
                        next(spec for spec in JOB_SPECS if spec["key"] == job_key)["required"]),
                    "requirements": f"{job.experience_min}-{job.experience_max} years; relevant role skills.",
                    "salary": f"₹{job.salary_min:g}–{job.salary_max:g} LPA",
                    "location": job.location,
                })
            app_rows[email].append(application)
            if created:
                for step, history_status in enumerate(history_statuses):
                    get_or_create(session, ApplicationStatusHistory,
                        {"application_id": application.id, "new_status": history_status}, {
                            "old_status": None if step == 0 else history_statuses[step - 1],
                            "changed_at": now - timedelta(days=10 - step),
                            "comment": f"Test workflow status: {history_status}",
                            "changed_by": user.id,
                        })

        seeded_interviews = []
        for email, application_list in app_rows.items():
            user = users[email]
            app = application_list[0]
            job = jobs["qa" if email.startswith("asha.") else "backend"]
            interview, _ = get_or_create(session, Interview,
                {"application_id": app.id, "round_name": "Technical 1"}, {
                "scheduled_at": now + timedelta(days=3), "mode": "ONLINE",
                "interviewer": "Priya Nair" if email.startswith("asha.") else "Arjun Rao",
                "meeting_link": "https://example.invalid/careertrack-test/meeting",
                "status": "SCHEDULED", "feedback": None,
            })
            seeded_interviews.append(interview)
            get_or_create(session, Note,
                {"user_id": user.id, "application_id": app.id, "title": f"[TEST] {job.title} interview notes"},
                {"content": "Prepare a concise project example; review required skills and questions."})
            get_or_create(session, Reminder,
                {"user_id": user.id, "application_id": app.id, "title": f"[TEST] Prepare for {job.title}"},
                {"reminder_type": "PREPARATION", "reminder_time": now + timedelta(days=2),
                 "status": "PENDING"})
            get_or_create(session, Bookmark, {"user_id": user.id, "job_id": job.id}, {"type": "SAVE"})
            get_or_create(session, Document,
                {"user_id": user.id, "application_id": app.id, "name": "[TEST] Submitted resume metadata"},
                {"file_url": f"https://example.invalid/careertrack-test/{email.split('@')[0]}-resume.pdf",
                 "doc_type": "RESUME"})
            get_or_create(session, UserInterviewQuestion,
                {"user_id": user.id, "application_id": app.id,
                 "question": f"[TEST] How would you explain your work related to {job.job_type}?"},
                {"category": job.job_type,
                 "asked_by": "[TEST] Cognizant" if email.startswith("asha.") else "[TEST] Deloitte",
                 "round": "Technical 1",
                 "difficulty": "MEDIUM", "my_answer": "I would explain the problem, approach, and result.",
                 "need_to_improve": "Add measurable outcomes."})
            get_or_create(session, ResumeMatch,
                {"user_id": user.id, "application_id": app.id},
                {"job_id": job.id, "resume_filename": "CareerTrack-Test-Resume-v1.pdf",
                 "match_percent": 75 if email.startswith("asha.") else 82,
                 "matched": ["Python", job.job_type], "missing": ["AWS"]})
            material = materials["qa" if email.startswith("asha.") else "backend"]
            get_or_create(session, MaterialBookmark,
                {"user_id": user.id, "material_id": material.id}, {})
            get_or_create(session, ApplicationEvent,
                {"application_id": app.id, "title": "[TEST] Recruiter follow-up recorded"},
                {"details": "Candidate confirmed interview availability.", "event_at": now - timedelta(days=1)})
            get_or_create(session, HRCall,
                {"application_id": app.id, "hr_name": "Priya Nair" if email.startswith("asha.") else "Arjun Rao",
                 "call_at": now - timedelta(days=1)},
                {"company_name": "[TEST] Cognizant" if email.startswith("asha.") else "[TEST] Deloitte",
                 "phone": "TEST ONLY", "discussion": "Discussed role and interview process.",
                 "next_round": "Technical 1", "interview_at": now + timedelta(days=3),
                 "notes": "Review the preserved job description before the call."})

        # Interview history is a separate table used by the application timeline.
        for interview in seeded_interviews:
            get_or_create(session, InterviewStatusHistory,
                {"interview_id": interview.id, "new_status": interview.status}, {
                    "old_status": None, "round_name": interview.round_name,
                    "scheduled_at": interview.scheduled_at, "mode": interview.mode,
                    "interviewer": interview.interviewer, "meeting_link": interview.meeting_link,
                    "changed_at": now - timedelta(hours=1), "feedback": interview.feedback,
                })

    with Session(engine) as session:
        return {name: session.query(model).count() for name, model in COUNT_MODELS.items()}


def _safe_database_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    seed_dir = (PROJECT_ROOT / ".testdata").resolve()
    if not resolved.is_relative_to(seed_dir) or resolved.suffix.casefold() not in {".db", ".sqlite", ".sqlite3"}:
        raise RuntimeError("Refusing seed target: --db-path must be a SQLite file inside the backend .testdata directory.")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed CareerTrack with isolated local test data.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH),
                        help="SQLite file under .testdata (default: .testdata/careertrack-seed.db)")
    args = parser.parse_args()
    path = _safe_database_path(args.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}", connect_args={"check_same_thread": False})
    try:
        counts = seed_data(engine)
        print("Seeded isolated CareerTrack SQLite test data (no .env database used):")
        for name, count in counts.items():
            print(f"  {name}: {count}")
        print("Test-only credentials (fresh database only):")
        print(f"  ADMIN {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        for email, name, password, _ in USERS:
            print(f"  USER  {email} / {password}")
        print("Rerunning this command is idempotent. The database contains TEST-labelled data only.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
