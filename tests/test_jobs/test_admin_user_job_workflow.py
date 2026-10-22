from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register the isolated test schema
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.application import Application
from app.models.job import Job
from app.models.user import User


def test_admin_job_publication_user_apply_and_ownership_workflow():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session()
    admin = User(name="Job Admin", email="job-admin@example.com",
                 password_hash=hash_password("workflow-admin-test-password"), role="ADMIN", status="ACTIVE")
    member = User(name="Job Member", email="job-member@example.com",
                  password_hash=hash_password("workflow-member-test-password"), role="USER", status="ACTIVE")
    other = User(name="Other Member", email="job-other@example.com",
                 password_hash=hash_password("workflow-other-test-password"), role="USER", status="ACTIVE")
    db.add_all([admin, member, other])
    db.commit()

    def db_override():
        yield db

    app.dependency_overrides[get_db] = db_override
    try:
        with TestClient(app) as client:
            # The mounted frontend must serve the same tracker scripts used by this checkout.
            page = client.get("/tracker/")
            assert page.status_code == 200
            assert "./api-client.js" in page.text
            assert page.text.index("./api-config.js") < page.text.index("./api-client.js")
            assert page.text.index("./app.js") < page.text.index("./extra.js")
            admin_script = client.get("/tracker/extra.js")
            assert admin_script.status_code == 200
            assert 'id="job-create"' in admin_script.text
            assert "api('/jobs'" in admin_script.text

            admin_login = client.post("/auth/login/json", json={
                "email": "job-admin@example.com", "password": "workflow-admin-test-password"
            })
            member_login = client.post("/auth/login/json", json={
                "email": "job-member@example.com", "password": "workflow-member-test-password"
            })
            other_login = client.post("/auth/login/json", json={
                "email": "job-other@example.com", "password": "workflow-other-test-password"
            })
            assert admin_login.status_code == member_login.status_code == other_login.status_code == 200
            admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
            member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}
            other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

            company_response = client.post("/companies", headers=admin_headers, json={
                "name": "Workflow Test Company", "website": "https://example.test",
                "industry": "Software", "location": "Remote",
            })
            assert company_response.status_code == 201, company_response.text
            company_id = company_response.json()["id"]

            payload = {
                "company_id": company_id,
                "title": "Workflow Test Backend Engineer",
                "description": "Build reliable Python APIs and maintain production services.",
                "location": "Remote", "work_mode": "REMOTE", "employment_type": "FULL_TIME",
                "salary_min": 12, "salary_max": 18,
                "application_url": "https://example.test/careers/backend",
                "skills": [{"name": "Python", "importance": "REQUIRED"}],
            }
            draft_response = client.post("/jobs", headers=admin_headers, json=payload)
            assert draft_response.status_code == 201, draft_response.text
            draft = draft_response.json()
            job_id = draft["id"]
            assert draft["status"] == "DRAFT"
            assert draft["created_by"] == db.query(User).filter_by(email="job-admin@example.com").one().id

            assert client.post("/jobs", headers=member_headers, json=payload).status_code == 403
            assert client.get("/jobs", headers=member_headers).json()["total"] == 0
            assert client.get(f"/jobs/{job_id}", headers=member_headers).status_code == 404

            edited = client.put(f"/jobs/{job_id}", headers=admin_headers, json={
                "title": "Workflow Test Senior Backend Engineer", "experience_min": 3,
                "experience_max": 6,
            })
            assert edited.status_code == 200, edited.text
            assert edited.json()["title"] == "Workflow Test Senior Backend Engineer"
            published = client.post(f"/jobs/{job_id}/publish", headers=admin_headers)
            assert published.status_code == 200, published.text
            assert published.json()["status"] == "ACTIVE"

            visible_jobs = client.get("/jobs", headers=member_headers, params={"q": "Senior Backend"})
            assert visible_jobs.status_code == 200
            assert [job["id"] for job in visible_jobs.json()["items"]] == [job_id]
            visible_detail = client.get(f"/jobs/{job_id}", headers=member_headers)
            assert visible_detail.status_code == 200
            assert visible_detail.json()["description"] == payload["description"]

            application_response = client.post("/applications", headers=member_headers, json={
                "job_id": job_id, "status": "APPLIED", "source": "CareerTrack job board",
            })
            assert application_response.status_code == 201, application_response.text
            application = application_response.json()
            assert application["user_id"] == db.query(User).filter_by(email="job-member@example.com").one().id
            assert application["job_id"] == job_id
            assert application["job_title"] == "Workflow Test Senior Backend Engineer"
            assert application["jd_text"] == payload["description"]

            member_applications = client.get("/applications", headers=member_headers)
            assert member_applications.status_code == 200
            assert [row["id"] for row in member_applications.json()] == [application["id"]]
            assert client.get("/applications", headers=other_headers).json() == []
            assert client.get(f"/applications/{application['id']}", headers=other_headers).status_code == 404
            assert db.query(func.count(Application.id)).filter_by(
                user_id=application["user_id"], job_id=job_id
            ).scalar() == 1
            assert db.query(func.count(Job.id)).filter_by(id=job_id).scalar() == 1

            closed = client.post(f"/jobs/{job_id}/close", headers=admin_headers)
            assert closed.status_code == 200, closed.text
            assert closed.json()["status"] == "CLOSED"
            assert client.get("/jobs", headers=member_headers).json()["total"] == 0
            assert client.get(f"/jobs/{job_id}", headers=member_headers).status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
