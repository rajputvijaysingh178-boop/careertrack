"""Seed repeatable demo data into the explicitly confirmed CareerTrack TEST Neon branch.

Dry-run by default. This script never creates or migrates schema.
Usage:
  Set CAREERTRACK_EXPECTED_TEST_HOST to the confirmed TEST host. The URL is read from
  CAREERTRACK_TEST_DATABASE_URL or .env DATABASE_URL; no URL is printed.
  python -m scripts.seed_test_data             # read-only preflight / plan
  python -m scripts.seed_test_data --apply     # add missing test demo records

Demo-only credentials:
  admin.demo@careertrack.test / DemoAdmin!2026
  user.demo@careertrack.test  / DemoUser!2026
"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timedelta

# Prevent the app's global engine from reading the normal .env database URL.
# The target engine below is constructed only from the explicit TEST variable.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("ENABLE_SCHEDULER", "false")

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from dotenv import dotenv_values

EXPECTED_TEST_HOST = "ep-wandering-mountain-b3xa8gdn.c-4.ap-southeast-1.aws.neon.tech"
ADMIN_EMAIL = "admin.demo@careertrack.test"
USER_EMAIL = "user.demo@careertrack.test"
ADMIN_PASSWORD = "DemoAdmin!2026"
USER_PASSWORD = "DemoUser!2026"
DEMO_COMPANY = "CareerTrack Demo (TEST ONLY)"

def target_url() -> str:
    url = (os.environ.get("CAREERTRACK_TEST_DATABASE_URL") or dotenv_values(".env").get("DATABASE_URL") or "").strip()
    expected = (os.environ.get("CAREERTRACK_EXPECTED_TEST_HOST") or
                os.environ.get("CAREERTRACK_ALEMBIC_EXPECTED_HOST") or "").strip().casefold().rstrip(".")
    if not url:
        raise RuntimeError("Set DATABASE_URL in .env or CAREERTRACK_TEST_DATABASE_URL in the process environment.")
    if not expected:
        raise RuntimeError("Set CAREERTRACK_EXPECTED_TEST_HOST to the confirmed TEST host before running this script.")
    if expected != EXPECTED_TEST_HOST.casefold():
        raise RuntimeError("CAREERTRACK_EXPECTED_TEST_HOST does not match the approved test host.")
    parsed = make_url(url)
    actual = (parsed.host or "").casefold().rstrip(".")
    if parsed.get_backend_name() != "postgresql" or actual != expected:
        raise RuntimeError("Refusing connection: only the explicitly confirmed PostgreSQL TEST host is allowed.")
    return url

def get_or_create(session, model, lookup: dict, values: dict):
    obj = session.query(model).filter_by(**lookup).first()
    if obj is not None:
        return obj, False
    obj = model(**lookup, **values)
    session.add(obj)
    session.flush()
    return obj, True

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed CareerTrack demo users and sample workflow in TEST only.")
    parser.add_argument("--apply", action="store_true", help="write missing demo rows; default is read-only")
    args = parser.parse_args()

    url = target_url()
    engine = create_engine(url, pool_pre_ping=True)
    try:
        from app.models import (  # register every mapped table
            User, Company, Job, Skill, JobSkill, Blog, Material, InterviewQuestion,
            Application, ApplicationStatusHistory, Interview, Note, Reminder, Bookmark,
        )
        required = {
            "users", "companies", "jobs", "skills", "job_skills", "blogs", "materials",
            "interview_questions", "applications", "application_status_history",
            "interviews", "notes", "reminders", "bookmarks",
        }
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        missing = sorted(required - existing)
        if missing:
            raise RuntimeError(
                "TEST schema is missing required tables: " + ", ".join(missing) +
                ". No data was written; reconcile the schema before seeding."
            )

        # Check the columns used by this seeder before opening a write transaction.
        expected_columns = {
            "users": {"id", "name", "email", "password_hash", "role", "status"},
            "companies": {"id", "name", "industry", "location", "status"},
            "jobs": {"id", "company_id", "title", "description", "status", "created_by"},
            "applications": {"id", "user_id", "job_id", "company_id", "status", "job_title", "company_name", "jd_text"},
        }
        for table, expected in expected_columns.items():
            actual = {column["name"] for column in inspector.get_columns(table)}
            if not expected.issubset(actual):
                raise RuntimeError(
                    f"TEST table {table} is missing expected columns: {', '.join(sorted(expected - actual))}. "
                    "No data was written."
                )

        with Session(engine) as session:
            # Read-only plan is the default. It also validates account roles if accounts already exist.
            admin_existing = session.query(User).filter_by(email=ADMIN_EMAIL).first()
            user_existing = session.query(User).filter_by(email=USER_EMAIL).first()
            if admin_existing and admin_existing.role != "ADMIN":
                raise RuntimeError(f"{ADMIN_EMAIL} exists but is not ADMIN; refusing to change its role.")
            if user_existing and user_existing.role != "USER":
                raise RuntimeError(f"{USER_EMAIL} exists but is not USER; refusing to change its role.")
            company_existing = session.query(Company).filter_by(name=DEMO_COMPANY).first()
            if company_existing and company_existing.status != "ACTIVE":
                raise RuntimeError("Existing test demo company is not ACTIVE; refusing to alter it.")
            job_titles = [
                "[TEST DEMO] Python Backend Engineer",
                "[TEST DEMO] Full Stack Engineer",
                "[TEST DEMO] QA Automation Engineer",
            ]
            jobs_existing = 0
            if company_existing:
                jobs_existing = session.query(Job).filter(
                    Job.company_id == company_existing.id, Job.title.in_(job_titles)
                ).count()
            plan = {
                "admin_user_to_create": int(admin_existing is None),
                "normal_user_to_create": int(user_existing is None),
                "demo_company_to_create": int(company_existing is None),
                "demo_jobs_to_create": len(job_titles) - jobs_existing,
                "mode": "APPLY" if args.apply else "READ-ONLY PLAN",
            }
            print("CareerTrack TEST demo data plan:")
            for key, value in plan.items():
                print(f"  {key}: {value}")
            if not args.apply:
                print("No changes made. Re-run with --apply to insert missing demo records.")
                return

            session.rollback()  # close the read-only planning transaction before beginning writes
            from app.core.security import hash_password
            now = datetime.utcnow()
            with session.begin():
                admin, _ = get_or_create(
                    session, User, {"email": ADMIN_EMAIL},
                    {"name": "CareerTrack Demo Admin", "password_hash": hash_password(ADMIN_PASSWORD),
                     "role": "ADMIN", "status": "ACTIVE", "location": "Hyderabad"},
                )
                user, _ = get_or_create(
                    session, User, {"email": USER_EMAIL},
                    {"name": "CareerTrack Demo User", "password_hash": hash_password(USER_PASSWORD),
                     "role": "USER", "status": "ACTIVE", "location": "Hyderabad"},
                )
                company, _ = get_or_create(
                    session, Company, {"name": DEMO_COMPANY},
                    {"industry": "Software / IT", "location": "Hyderabad", "company_size": "TEST",
                     "website": "https://example.com", "description": "TEST-ONLY sample company",
                     "status": "ACTIVE"},
                )

                skill_specs = [
                    ("Python", "Backend"), ("FastAPI", "Backend"), ("PostgreSQL", "Data"),
                    ("SQL", "Data"), ("React", "Frontend"), ("Playwright", "Testing"),
                ]
                skills = {}
                for name, category in skill_specs:
                    skill, _ = get_or_create(session, Skill, {"name": name}, {"category": category})
                    skills[name] = skill

                job_specs = [
                    (job_titles[0], "Backend", "Python FastAPI PostgreSQL SQL", ["Python", "FastAPI", "PostgreSQL", "SQL"]),
                    (job_titles[1], "Full Stack", "Python React SQL", ["Python", "React", "SQL"]),
                    (job_titles[2], "QA", "Python Playwright API testing", ["Python", "Playwright"]),
                ]
                jobs = {}
                for index, (title, job_type, skill_text, skill_names) in enumerate(job_specs):
                    job, _ = get_or_create(
                        session, Job, {"company_id": company.id, "title": title},
                        {"description": f"TEST DEMO ONLY. Build and test applications using {skill_text}.",
                         "location": "Hyderabad", "work_mode": "HYBRID", "employment_type": "FULL_TIME",
                         "job_type": job_type, "experience_min": 0, "experience_max": 3,
                         "salary_min": 4, "salary_max": 10,
                         "application_url": "https://example.com/test-job",
                         "posted_date": date.today(), "expiry_date": date.today() + timedelta(days=30),
                         "status": "ACTIVE", "created_by": admin.id},
                    )
                    jobs[title] = job
                    for skill_name in skill_names:
                        link = session.query(JobSkill).filter_by(job_id=job.id, skill_id=skills[skill_name].id).first()
                        if not link:
                            session.add(JobSkill(job_id=job.id, skill_id=skills[skill_name].id, importance="REQUIRED"))

                blog, _ = get_or_create(
                    session, Blog, {"slug": "careertrack-test-python-interview-guide"},
                    {"title": "[TEST DEMO] Python Interview Guide",
                     "content": "TEST-ONLY guide covering Python, FastAPI, SQL and API design.",
                     "category": "Python", "tags": ["Python", "Interview", "Backend"],
                     "author_id": admin.id, "status": "PUBLISHED", "published_at": now},
                )
                material, _ = get_or_create(
                    session, Material, {"title": "[TEST DEMO] FastAPI Learning Resource"},
                    {"description": "TEST-ONLY sample learning link.", "type": "ARTICLE",
                     "file_url": "https://fastapi.tiangolo.com/tutorial/",
                     "skill_id": skills["FastAPI"].id, "job_id": jobs[job_titles[0]].id,
                     "company_id": company.id, "role": "Python Backend Engineer",
                     "interview_round": "Technical 1", "created_by": admin.id},
                )
                question, _ = get_or_create(
                    session, InterviewQuestion, {"question": "[TEST DEMO] Explain FastAPI dependency injection."},
                    {"company_id": company.id, "job_id": jobs[job_titles[0]].id,
                     "skill_id": skills["FastAPI"].id, "category": "FastAPI", "difficulty": "MEDIUM",
                     "experience_level": "0-3 Years", "round": "Technical 1",
                     "expected_topics": ["Dependencies", "Testing", "Separation of concerns"],
                     "answer": "Dependencies provide reusable request-scoped logic.",
                     "created_by": admin.id},
                )

                app_title = job_titles[0]
                application, created = get_or_create(
                    session, Application, {"user_id": user.id, "job_id": jobs[app_title].id},
                    {"company_id": company.id, "applied_date": now, "status": "INTERVIEW_SCHEDULED",
                     "source": "CareerTrack Test Demo", "application_url": "https://example.com/test-job",
                     "job_title": app_title, "company_name": company.name,
                     "jd_text": jobs[app_title].description,
                     "skills": "Python, FastAPI, PostgreSQL, SQL",
                     "requirements": "TEST DEMO ONLY; 0-3 years; API development",
                     "salary": "4-10 LPA", "location": "Hyderabad"},
                )
                if created:
                    session.add_all([
                        ApplicationStatusHistory(application_id=application.id, old_status=None,
                            new_status="APPLIED", changed_at=now, comment="Demo application created", changed_by=user.id),
                        ApplicationStatusHistory(application_id=application.id, old_status="APPLIED",
                            new_status="INTERVIEW_SCHEDULED", changed_at=now,
                            comment="Demo interview scheduled", changed_by=user.id),
                    ])
                interview, _ = get_or_create(
                    session, Interview, {"application_id": application.id, "round_name": "Technical 1"},
                    {"scheduled_at": now + timedelta(days=2), "mode": "ONLINE",
                     "interviewer": "Demo Interviewer", "meeting_link": "https://example.com/meeting",
                     "status": "SCHEDULED", "feedback": None},
                )
                note, _ = get_or_create(
                    session, Note, {"user_id": user.id, "application_id": application.id,
                                    "title": "[TEST DEMO] Preparation Notes"},
                    {"content": "Review Python OOP, FastAPI dependencies, SQL joins, and REST API design."},
                )
                reminder, _ = get_or_create(
                    session, Reminder, {"user_id": user.id, "application_id": application.id,
                                        "title": "[TEST DEMO] Prepare for technical interview"},
                    {"reminder_type": "INTERVIEW", "reminder_time": now + timedelta(days=1), "status": "PENDING"},
                )
                bookmark, _ = get_or_create(
                    session, Bookmark, {"user_id": user.id, "job_id": jobs[job_titles[1]].id},
                    {"type": "SAVE"},
                )
            print("Demo data seeded successfully into the confirmed TEST database.")
            print(f"Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
            print(f"User login:  {USER_EMAIL} / {USER_PASSWORD}")
            print("Demo records are clearly labelled TEST DEMO ONLY.")
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
