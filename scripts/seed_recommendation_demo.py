"""Idempotently add clearly labelled recommendation demo data to the confirmed TEST database.

This script never creates schema. Run without --apply to see a read-only plan. Writes require
CAREERTRACK_TEST_DATABASE_URL, CAREERTRACK_EXPECTED_TEST_HOST, and the explicit --apply flag.
"""
from __future__ import annotations

import argparse
import os
from datetime import date
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


CONFIRMED_TEST_HOST = "ep-wandering-mountain-b3xa8gdn.c-4.ap-southeast-1.aws.neon.tech"
DEMO_COMPANY = "CareerTrack Demo (TEST ONLY)"
DEMO_SKILLS = (
    ("Python", "Backend"),
    ("FastAPI", "Backend"),
    ("SQL", "Data"),
    ("React", "Frontend"),
    ("AWS", "Cloud"),
)
DEMO_JOBS = (
    {
        "title": "[TEST DEMO] Python Backend Engineer",
        "description": "TEST DEMO ONLY. Build Python APIs with FastAPI and SQL. Not a real vacancy.",
        "job_type": "Backend",
        "skills": (("Python", "REQUIRED"), ("FastAPI", "REQUIRED"), ("SQL", "PREFERRED")),
    },
    {
        "title": "[TEST DEMO] Full Stack Engineer",
        "description": "TEST DEMO ONLY. Build a full stack app using React, Python, and SQL. Not a real vacancy.",
        "job_type": "Full Stack",
        "skills": (("Python", "REQUIRED"), ("React", "REQUIRED"), ("SQL", "PREFERRED")),
    },
    {
        "title": "[TEST DEMO] Cloud Application Engineer",
        "description": "TEST DEMO ONLY. Operate Python services and cloud infrastructure on AWS. Not a real vacancy.",
        "job_type": "Cloud",
        "skills": (("Python", "PREFERRED"), ("AWS", "REQUIRED")),
    },
)


def guarded_test_database_url(environ=None) -> str:
    env = os.environ if environ is None else environ
    url = (env.get("CAREERTRACK_TEST_DATABASE_URL") or "").strip()
    expected = (env.get("CAREERTRACK_EXPECTED_TEST_HOST") or "").strip().lower()
    if not url:
        raise RuntimeError("CAREERTRACK_TEST_DATABASE_URL is required; refusing to use application configuration.")
    if expected != CONFIRMED_TEST_HOST:
        raise RuntimeError("CAREERTRACK_EXPECTED_TEST_HOST must exactly match the confirmed test host.")
    try:
        parsed = make_url(url)
    except Exception as exc:
        raise RuntimeError("CAREERTRACK_TEST_DATABASE_URL is invalid.") from exc
    actual = (parsed.host or "").lower()
    if parsed.drivername.split("+")[0] not in {"postgres", "postgresql"} or actual != expected:
        raise RuntimeError("Refusing database access: URL host or database type is not the confirmed test target.")
    return url


def _plan(db: Session) -> dict:
    from app.models.company import Company
    from app.models.job import Job
    from app.models.skill import JobSkill, Skill

    company = db.query(Company).filter(Company.name == DEMO_COMPANY).first()
    if company and company.status != "ACTIVE":
        raise RuntimeError("The existing demo company is not ACTIVE; refusing to change it.")
    skill_rows = db.query(Skill).all()
    skill_by_name = {row.name.strip().casefold(): row for row in skill_rows}
    missing_skills = [name for name, _ in DEMO_SKILLS if name.casefold() not in skill_by_name]
    jobs_to_create = links_to_create = 0
    for spec in DEMO_JOBS:
        existing = None
        if company:
            existing = (db.query(Job).filter_by(company_id=company.id, title=spec["title"]).first())
        if existing is None:
            jobs_to_create += 1
            links_to_create += len(spec["skills"])
            continue
        if existing.status not in {"ACTIVE", "PUBLISHED"} or (existing.expiry_date and existing.expiry_date < date.today()):
            raise RuntimeError(f"Existing demo job {spec['title']!r} is not eligible; refusing to alter it.")
        linked_ids = {row[0] for row in db.query(JobSkill.skill_id).filter_by(job_id=existing.id).all()}
        for name, _ in spec["skills"]:
            skill = skill_by_name.get(name.casefold())
            if skill is None or skill.id not in linked_ids:
                links_to_create += 1
    return {
        "company_to_create": int(company is None),
        "skills_to_create": len(missing_skills),
        "jobs_to_create": jobs_to_create,
        "job_skill_links_to_create": links_to_create,
    }


def seed_demo_jobs(db: Session, *, apply: bool = False) -> dict:
    """Plan without writes by default; apply only adds missing demo rows/links."""
    plan = _plan(db)
    if not apply:
        return plan

    from app.models.company import Company
    from app.models.job import Job
    from app.models.skill import JobSkill, Skill

    company = db.query(Company).filter(Company.name == DEMO_COMPANY).first()
    if company is None:
        company = Company(name=DEMO_COMPANY, status="ACTIVE", industry="Technology", location="Remote")
        db.add(company)
        db.flush()

    skill_by_name = {row.name.strip().casefold(): row for row in db.query(Skill).all()}
    for name, category in DEMO_SKILLS:
        if name.casefold() not in skill_by_name:
            skill = Skill(name=name, category=category)
            db.add(skill)
            db.flush()
            skill_by_name[name.casefold()] = skill

    for spec in DEMO_JOBS:
        job = db.query(Job).filter_by(company_id=company.id, title=spec["title"]).first()
        if job is None:
            job = Job(
                company_id=company.id,
                title=spec["title"],
                description=spec["description"],
                location="Remote",
                work_mode="REMOTE",
                employment_type="FULL_TIME",
                job_type=spec["job_type"],
                experience_min=1,
                status="ACTIVE",
                posted_date=date.today(),
            )
            db.add(job)
            db.flush()
        linked_ids = {row[0] for row in db.query(JobSkill.skill_id).filter_by(job_id=job.id).all()}
        for name, importance in spec["skills"]:
            skill = skill_by_name[name.casefold()]
            if skill.id not in linked_ids:
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, importance=importance))
                linked_ids.add(skill.id)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--dry-run", action="store_true", help="show the guarded plan without writing (default)")
    action.add_argument("--apply", action="store_true", help="commit the explicitly guarded test-only demo rows")
    args = parser.parse_args()

    url = guarded_test_database_url()
    # Keep any module-level application engine pointed at the same guarded test URL.
    os.environ["DATABASE_URL"] = url
    from app.core.database import Base  # noqa: F401 - registers model metadata

    engine_url = make_url(url).set(drivername="postgresql+psycopg")
    engine = create_engine(engine_url, pool_pre_ping=True)
    try:
        required = {"companies", "jobs", "skills", "job_skills"}
        missing = required - set(inspect(engine).get_table_names())
        if missing:
            raise RuntimeError(f"Required tables are missing: {', '.join(sorted(missing))}. No schema was created.")
        with Session(engine) as db:
            changes = seed_demo_jobs(db, apply=args.apply)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        mode = "Applied" if args.apply else "Dry run; no rows written"
        print(mode + ": " + ", ".join(f"{key}={value}" for key, value in changes.items()))
        print("The user's skill profile was not changed; re-save supported skills after applying this seed.")
        return 0
    except Exception:
        engine.dispose()
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
