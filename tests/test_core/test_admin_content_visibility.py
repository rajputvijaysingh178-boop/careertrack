from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register model metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


def test_admin_published_content_is_visible_to_users_and_writes_are_restricted():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    admin = User(name="Content Admin", email="content-admin@example.com",
                 password_hash=hash_password("content-admin-password"), role="ADMIN", status="ACTIVE")
    member = User(name="Content Member", email="content-member@example.com",
                  password_hash=hash_password("content-member-password"), role="USER", status="ACTIVE")
    db.add_all([admin, member])
    db.commit()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    admin_headers = {"Authorization": f"Bearer {create_access_token(str(admin.id), 'ADMIN')}"}
    member_headers = {"Authorization": f"Bearer {create_access_token(str(member.id), 'USER')}"}
    try:
        with TestClient(app) as client:
            company = client.post("/companies", headers=admin_headers,
                                  json={"name": "Visibility Test Co"})
            assert company.status_code == 201, company.text

            job = client.post("/jobs", headers=admin_headers, json={
                "company_id": company.json()["id"],
                "title": "Visibility Test Python Engineer",
                "description": "Build Python APIs and maintain reliable services.",
                "skills": [{"name": "Python", "importance": "REQUIRED"}],
            })
            assert job.status_code == 201, job.text
            job_id = job.json()["id"]
            assert client.get("/jobs", headers=member_headers).json()["total"] == 0
            assert client.get(f"/jobs/{job_id}", headers=member_headers).status_code == 404

            published = client.post(f"/jobs/{job_id}/publish", headers=admin_headers)
            assert published.status_code == 200, published.text
            member_jobs = client.get("/jobs", headers=member_headers)
            assert member_jobs.status_code == 200
            assert job_id in {row["id"] for row in member_jobs.json()["items"]}
            assert client.get(f"/jobs/{job_id}", headers=member_headers).json()["status"] == "ACTIVE"
            assert client.post("/jobs", headers=member_headers, json={
                "company_id": company.json()["id"],
                "title": "Unauthorized Job",
                "description": "This member must not be able to create a job.",
            }).status_code == 403

            draft = client.post("/blogs", headers=admin_headers, json={
                "title": "Visibility Test Draft",
                "content": "This draft is hidden from normal users.",
                "status": "DRAFT",
            })
            assert draft.status_code == 201, draft.text
            assert client.get(f"/blogs/{draft.json()['slug']}", headers=member_headers).status_code == 404
            published_blog = client.put(f"/blogs/{draft.json()['id']}", headers=admin_headers,
                                        json={"status": "PUBLISHED"})
            assert published_blog.status_code == 200, published_blog.text
            member_blogs = client.get("/blogs", headers=member_headers)
            assert draft.json()["slug"] in {row["slug"] for row in member_blogs.json()["items"]}

            question = client.post("/interview-questions", headers=admin_headers, json={
                "job_id": job_id, "category": "Python", "question": "How do Python generators work?",
                "difficulty": "MEDIUM",
            })
            assert question.status_code == 201, question.text
            visible_questions = client.get("/interview-questions", headers=member_headers)
            assert question.json()["id"] in {row["id"] for row in visible_questions.json()["items"]}

            material = client.post("/materials", headers=admin_headers, json={
                "title": "Python reference", "type": "ARTICLE", "file_url": "https://example.com/python",
                "job_id": job_id,
            })
            assert material.status_code == 201, material.text
            visible_materials = client.get("/materials", headers=member_headers)
            assert material.json()["id"] in {row["id"] for row in visible_materials.json()["items"]}
            assert client.get("/admin/dashboard", headers=member_headers).status_code == 403
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
