from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all model metadata
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.application import ApplicationStatusHistory
from app.models.company import Company
from app.models.job import Job
from app.models.skill import JobSkill, Skill
from app.models.user import User
from app.core.security import hash_password


def test_authenticated_tracker_and_rule_based_ai_smoke(monkeypatch):
    """Exercise key browser API flows against an isolated in-memory SQLite database."""
    monkeypatch.setattr(settings, "LLM_API_KEY", "")
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session()

    admin = User(
        name="Smoke Admin", email="smoke-admin@example.com",
        password_hash=hash_password("smoke-test-password"), role="ADMIN", status="ACTIVE",
    )
    company = Company(name="SMOKE TEST Company", status="ACTIVE")
    db.add_all([admin, company])
    db.flush()
    python = Skill(name="Python", category="Backend")
    db.add(python)
    db.flush()
    job = Job(
        company_id=company.id, title="SMOKE TEST Backend Engineer",
        description="Build Python APIs and backend services using FastAPI.",
        status="ACTIVE", work_mode="REMOTE", employment_type="FULL_TIME",
        job_type="Backend", experience_min=2,
    )
    recommended_job = Job(
        company_id=company.id, title="SMOKE TEST Platform Engineer",
        description="Build Python platform services and APIs.",
        status="ACTIVE", work_mode="REMOTE", employment_type="FULL_TIME",
        job_type="Backend", experience_min=2,
    )
    db.add_all([job, recommended_job])
    db.flush()
    db.add_all([
        JobSkill(job_id=job.id, skill_id=python.id, importance="REQUIRED"),
        JobSkill(job_id=recommended_job.id, skill_id=python.id, importance="REQUIRED"),
    ])
    db.commit()
    job_id = job.id
    recommended_job_id = recommended_job.id

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            login = client.post(
                "/auth/login/json",
                json={"email": admin.email, "password": "smoke-test-password"},
            )
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            me = client.get("/auth/me", headers=headers)
            assert me.status_code == 200, me.text
            assert me.json()["id"] == admin.id and me.json()["role"] == "ADMIN"

            jobs = client.get("/jobs?limit=20", headers=headers)
            assert jobs.status_code == 200, jobs.text
            assert any(item["id"] == job_id for item in jobs.json()["items"])
            detail = client.get(f"/jobs/{job_id}", headers=headers)
            assert detail.status_code == 200 and detail.json()["title"] == job.title

            created = client.post(
                "/applications", headers=headers,
                json={"job_id": job_id, "status": "APPLIED", "source": "SMOKE TEST"},
            )
            assert created.status_code == 201, created.text
            application_id = created.json()["id"]
            changed = client.post(
                f"/applications/{application_id}/status", headers=headers,
                json={"status": "APPLICATION_VIEWED", "comment": "SMOKE TEST transition"},
            )
            assert changed.status_code == 200, changed.text
            assert changed.json()["status"] == "APPLICATION_VIEWED"
            kanban = client.get("/applications/kanban", headers=headers)
            assert kanban.status_code == 200 and application_id in {
                row["id"] for row in kanban.json()["APPLICATION_VIEWED"]
            }
            listed = client.get("/applications?limit=200", headers=headers)
            assert listed.status_code == 200
            assert [row["id"] for row in listed.json()] == [application_id]
            status_history = db.query(ApplicationStatusHistory).filter_by(
                application_id=application_id
            ).all()
            assert [row.new_status for row in status_history] == ["APPLIED", "APPLICATION_VIEWED"]

            interview = client.post(
                f"/interviews/applications/{application_id}", headers=headers,
                json={"round_name": "SMOKE TEST Recruiter screen",
                      "scheduled_at": (datetime.now() + timedelta(days=2)).isoformat()},
            )
            assert interview.status_code == 201, interview.text
            interviews = client.get(
                f"/interviews/applications/{application_id}", headers=headers
            )
            assert interviews.status_code == 200 and len(interviews.json()) == 1

            bookmark = client.post(
                "/bookmarks", headers=headers, json={"job_id": job_id, "type": "SAVE"}
            )
            assert bookmark.status_code == 201, bookmark.text
            bookmarks = client.get("/bookmarks", headers=headers)
            assert bookmarks.status_code == 200
            assert any(row["id"] == bookmark.json()["id"] for row in bookmarks.json())

            dashboard = client.get("/dashboard/analytics", headers=headers)
            assert dashboard.status_code == 200, dashboard.text
            assert dashboard.json()["total_applications"] == len(listed.json()) == 1
            assert dashboard.json()["by_status"] == {"APPLICATION_VIEWED": 1}
            assert dashboard.json()["interview_rounds"] == len(interviews.json()) == 1

            jd = client.post(
                "/jd-analyzer/analyze", headers=headers,
                json={"jd_text": "Python FastAPI engineer building reliable APIs.", "use_ai": True},
            )
            assert jd.status_code == 200, jd.text
            assert jd.json()["ai_used"] is False
            assert jd.json().get("ai_error")
            assert "Python" in {skill["name"] for skill in jd.json()["skills"]}

            match = client.post(
                "/resume-match", headers=headers,
                data={"job_id": str(job_id)},
                files={"file": ("smoke_resume.txt", b"Python FastAPI backend engineer", "text/plain")},
            )
            assert match.status_code == 200, match.text
            assert match.json()["match_percent"] == 100

            profile = client.put(
                "/recommendations/my-skills", headers=headers, json={"skills": ["Python"]}
            )
            assert profile.status_code == 200, profile.text
            recommendations = client.get("/recommendations/jobs", headers=headers)
            assert recommendations.status_code == 200
            assert any(row["job_id"] == recommended_job_id for row in recommendations.json()["jobs"])

            plan = client.post(
                "/prep/plan", headers=headers,
                json={"job_id": job_id, "days": 7, "use_ai": True},
            )
            assert plan.status_code == 200, plan.text
            assert plan.json()["source"] == "rules"
            assert isinstance(plan.json()["days"], int)
            assert isinstance(plan.json()["plan"], list)
            assert plan.json()["days"] == len(plan.json()["plan"]) == 7
            assert len(plan.json()["plan"]) == 7
            assert "Mock interview" in plan.json()["plan"][-1]["title"]

            tracker_page = client.get("/tracker/")
            assert "./prep-plan.js?v=prep-plan-1" in tracker_page.text
            plan_renderer = client.get("/tracker/prep-plan.js")
            assert plan_renderer.status_code == 200
            assert "renderPrepPlanResponse" in plan_renderer.text
            tracker_js = client.get("/tracker/extra.js")
            assert tracker_js.status_code == 200
            assert "renderPrepPlanResponse(plan,esc)" in tracker_js.text
            assert "(plan.days||plan.plan||[]).map" not in tracker_js.text
            assert "api('/applications?limit=200')" in tracker_js.text
            assert "api('/prep/workspace'" in tracker_js.text

            ad_hoc = client.post(
                "/applications", headers=headers,
                json={"job_title": "SMOKE TEST Python Data Engineer", "status": "SAVED"},
            )
            assert ad_hoc.status_code == 201, ad_hoc.text
            ad_hoc_workspace = client.get(
                f"/prep/applications/{ad_hoc.json()['id']}", headers=headers
            )
            assert ad_hoc_workspace.status_code == 200, ad_hoc_workspace.text
            assert ad_hoc_workspace.json()["job"]["title"] == "SMOKE TEST Python Data Engineer"
            assert "Python" in {item["name"] for item in ad_hoc_workspace.json()["skills"]}

            custom_workspace = client.post(
                "/prep/workspace", headers=headers,
                json={"role_title": "SMOKE TEST Python Site Reliability Engineer",
                      "jd_text": "Build reliable Python services and automate incident response."},
            )
            assert custom_workspace.status_code == 200, custom_workspace.text
            assert custom_workspace.json()["workspace"]["job"]["title"] == \
                "SMOKE TEST Python Site Reliability Engineer"
            assert "Python" in {
                item["name"] for item in custom_workspace.json()["skill_gap"]["matched"]
            }
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
