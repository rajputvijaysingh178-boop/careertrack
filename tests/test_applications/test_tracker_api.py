from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # register all tables
from app.core.database import Base, get_db
from app.core.dependencies import get_current_user
from app.main import app
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.application import Application
from app.models.skill import JobSkill, Skill


def test_tracker_api_round_trip_and_static_frontend():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    owner = User(name="Owner", email="api-owner@example.test", password_hash="hash")
    other = User(name="Other", email="api-other@example.test", password_hash="hash")
    db.add_all([owner, other])
    db.commit()
    owner_id = owner.id
    other_id = other.id
    user = db.get(User, owner_id)
    company = Company(name="API Company")
    db.add(company)
    db.flush()
    job = Job(company_id=company.id, title="API Job", description="A detailed description for this role.",
              status="ACTIVE", work_mode="REMOTE", employment_type="FULL_TIME", job_type="Backend",
              experience_min=2, salary_min=10)
    db.add(job)
    db.commit()
    job_id = job.id
    python = Skill(name="Python", category="Backend")
    db.add(python)
    db.flush()
    db.add(JobSkill(job_id=job_id, skill_id=python.id, importance="REQUIRED"))
    db.commit()

    def db_override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as client:
            assert client.get("/tracker/").status_code == 200
            frontend = client.get("/tracker/extra.js")
            assert frontend.status_code == 200
            assert 'name="company_id"' in frontend.text and "showJobDetails" in frontend.text
            filtered = client.get("/jobs", params={"q": "API Job", "work_mode": "REMOTE",
                                                    "employment_type": "FULL_TIME", "skills": "Python",
                                                    "skills_match": "all", "experience": 2, "salary_min": 8})
            assert filtered.status_code == 200, filtered.text
            assert [job["id"] for job in filtered.json()["items"]] == [job_id]
            assert client.get(f"/jobs/{job_id}").json()["description"] == "A detailed description for this role."
            created = client.post("/applications", json={"job_title": "Platform Engineer", "status": "APPLIED"})
            assert created.status_code == 201, created.text
            application_id = created.json()["id"]
            foreign_application = Application(user_id=other_id, job_title="Private application", status="APPLIED")
            db.add(foreign_application)
            db.commit()
            assert client.post("/documents", json={"application_id": foreign_application.id,
                "name": "Private resume", "file_url": "https://example.test/resume.pdf"}).status_code == 404
            assert client.post("/interview-questions/mine", json={
                "application_id": foreign_application.id,
                "question": "How do you design a reliable API?"
            }).status_code == 404
            bookmark = client.post("/bookmarks", json={"job_id": job_id, "type": "SAVE"})
            assert bookmark.status_code == 201, bookmark.text
            ignored = client.put(f"/bookmarks/{bookmark.json()['id']}", json={"type": "IGNORE"})
            assert ignored.status_code == 200 and ignored.json()["type"] == "IGNORE"
            restored = client.put(f"/bookmarks/{bookmark.json()['id']}", json={"type": "SAVE"})
            assert restored.status_code == 200 and restored.json()["type"] == "SAVE"
            jd_result = client.post("/jd-analyzer/analyze", json={
                "jd_text": "Python engineer building services and APIs for customers.", "use_ai": False
            })
            assert jd_result.status_code == 200, jd_result.text
            assert any(item["name"].lower() == "python" for item in jd_result.json()["skills"])
            match_result = client.post("/resume-match", data={
                "job_id": str(job_id), "resume_text": "Experienced Python API developer"
            })
            assert match_result.status_code == 200, match_result.text
            assert match_result.json()["match_percent"] == 100
            skill_update = client.put("/recommendations/my-skills", json={"skills": ["Python"]})
            assert skill_update.status_code == 200, skill_update.text
            recommended = client.get("/recommendations/jobs")
            assert recommended.status_code == 200, recommended.text
            assert recommended.json()["jobs"][0]["job_id"] == job_id
            document = client.post("/documents", json={"application_id": application_id,
                "name": "Resume", "file_url": "https://example.test/resume.pdf", "doc_type": "RESUME"})
            assert document.status_code == 201, document.text
            round_response = client.post(f"/interviews/applications/{application_id}", json={
                "round_name": "Recruiter call", "mode": "PHONE", "feedback": "Availability discussed"
            })
            assert round_response.status_code == 201, round_response.text
            round_id = round_response.json()["id"]
            updated = client.put(f"/interviews/{round_id}", json={
                "status": "COMPLETED", "feedback": "Move to technical round"
            })
            assert updated.status_code == 200
            call = client.post(f"/applications/{application_id}/hr-calls", json={
                "hr_name": "Priya", "phone": "555-0100", "discussion": "Technical round scheduled",
                "next_round": "Technical interview"
            })
            assert call.status_code == 201, call.text
            event = client.post(f"/applications/{application_id}/events", json={
                "title": "Sent portfolio", "details": "Sent updated work samples"
            })
            assert event.status_code == 201, event.text
            assert client.get(f"/applications/{application_id}/hr-calls").json()[0]["hr_name"] == "Priya"
            history = client.get(f"/interviews/{round_id}/history")
            assert [row["new_status"] for row in history.json()] == ["SCHEDULED", "COMPLETED"]
            timeline = client.get(f"/applications/{application_id}/timeline").json()
            assert timeline["application"]["status"] == "APPLIED"
            assert {row["type"] for row in timeline["events"]} >= {"status", "interview", "hr_call", "note"}
            assert timeline["events"]
            assert client.get("/applications/kanban").status_code == 200
            linked = client.post("/applications", json={"job_id": job_id, "status": "APPLIED"})
            assert linked.status_code == 201, linked.text
            linked_id = linked.json()["id"]
            prep = client.get(f"/prep/applications/{linked_id}")
            assert prep.status_code == 200, prep.text
            assert prep.json()["application_id"] == linked_id
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
