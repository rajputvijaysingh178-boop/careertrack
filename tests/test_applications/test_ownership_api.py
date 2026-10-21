from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register model metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.company import Company
from app.models.job import Job
from app.models.user import User


def test_application_resources_are_isolated_between_authenticated_users():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session()
    owner_a = User(name="Owner A", email="owner-a@example.com", password_hash=hash_password("test-password-a"))
    owner_b = User(name="Owner B", email="owner-b@example.com", password_hash=hash_password("test-password-b"))
    company = Company(name="Ownership Test Company")
    db.add_all([owner_a, owner_b, company])
    db.flush()
    job = Job(company_id=company.id, title="Ownership Test Role", description="Role description for isolation tests.",
              status="ACTIVE")
    db.add(job)
    db.commit()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    headers_a = {"Authorization": f"Bearer {create_access_token(str(owner_a.id), 'USER')}"}
    headers_b = {"Authorization": f"Bearer {create_access_token(str(owner_b.id), 'USER')}"}
    try:
        with TestClient(app) as client:
            app_a = client.post("/applications", headers=headers_a,
                                json={"job_title": "Private Role A", "status": "APPLIED"}).json()
            app_b = client.post("/applications", headers=headers_b,
                                json={"job_title": "Private Role B", "status": "APPLIED"}).json()
            assert client.get("/applications", headers=headers_b).json()[0]["id"] == app_b["id"]
            assert client.get(f"/applications/{app_a['id']}", headers=headers_b).status_code == 404

            round_a = client.post(f"/interviews/applications/{app_a['id']}", headers=headers_a,
                                  json={"round_name": "Private Round A"}).json()
            round_b = client.post(f"/interviews/applications/{app_b['id']}", headers=headers_b,
                                  json={"round_name": "Private Round B"}).json()
            assert client.get(f"/interviews/applications/{app_a['id']}", headers=headers_b).status_code == 404
            assert client.put(f"/interviews/{round_a['id']}", headers=headers_b,
                              json={"feedback": "Unauthorized"}).status_code == 404
            assert client.get(f"/interviews/{round_a['id']}/history", headers=headers_b).status_code == 404
            assert client.delete(f"/interviews/{round_a['id']}", headers=headers_b).status_code == 404
            assert client.get(f"/interviews/applications/{app_b['id']}", headers=headers_b).json()[0]["id"] == round_b["id"]

            note_a = client.post("/notes", headers=headers_a,
                                 json={"application_id": app_a["id"], "title": "Private note A"}).json()
            note_b = client.post("/notes", headers=headers_b,
                                 json={"application_id": app_b["id"], "title": "Private note B"}).json()
            assert client.get("/notes", headers=headers_b).json()[0]["id"] == note_b["id"]
            assert client.get("/notes", headers=headers_b, params={"application_id": app_a["id"]}).status_code == 404
            assert client.put(f"/notes/{note_a['id']}", headers=headers_b,
                              json={"title": "Unauthorized"}).status_code == 404
            assert client.delete(f"/notes/{note_a['id']}", headers=headers_b).status_code == 404

            doc_a = client.post("/documents", headers=headers_a, json={
                "application_id": app_a["id"], "name": "Private document A",
                "file_url": "https://example.com/private-a.pdf",
            }).json()
            doc_b = client.post("/documents", headers=headers_b, json={
                "application_id": app_b["id"], "name": "Private document B",
                "file_url": "https://example.com/private-b.pdf",
            }).json()
            assert [row["id"] for row in client.get("/documents", headers=headers_b).json()] == [doc_b["id"]]
            assert client.get("/documents", headers=headers_b,
                             params={"application_id": app_a["id"]}).status_code == 404
            assert client.delete(f"/documents/{doc_a['id']}", headers=headers_b).status_code == 404

            reminder_a = client.post("/reminders", headers=headers_a, json={
                "application_id": app_a["id"], "title": "Private reminder A", "reminder_time": "2030-01-01T12:00:00Z",
            }).json()
            reminder_b = client.post("/reminders", headers=headers_b, json={
                "application_id": app_b["id"], "title": "Private reminder B", "reminder_time": "2030-01-02T12:00:00Z",
            }).json()
            assert [row["id"] for row in client.get("/reminders", headers=headers_b).json()] == [reminder_b["id"]]
            assert client.put(f"/reminders/{reminder_a['id']}", headers=headers_b,
                              json={"title": "Unauthorized"}).status_code == 404
            assert client.delete(f"/reminders/{reminder_a['id']}", headers=headers_b).status_code == 404
            assert client.post("/reminders", headers=headers_b, json={
                "application_id": app_a["id"], "title": "Cross-owner reminder",
                "reminder_time": "2030-01-03T12:00:00Z",
            }).status_code == 404

            bookmark_a = client.post("/bookmarks", headers=headers_a,
                                     json={"job_id": job.id, "type": "SAVE"}).json()
            bookmark_b = client.post("/bookmarks", headers=headers_b,
                                     json={"job_id": job.id, "type": "SAVE"}).json()
            assert [row["id"] for row in client.get("/bookmarks", headers=headers_b).json()] == [bookmark_b["id"]]
            assert client.put(f"/bookmarks/{bookmark_a['id']}", headers=headers_b,
                              json={"type": "IGNORE"}).status_code == 404
            assert client.delete(f"/bookmarks/{bookmark_a['id']}", headers=headers_b).status_code == 404

            question_a = client.post("/interview-questions/mine", headers=headers_a, json={
                "application_id": app_a["id"], "question": "Private interview question A?",
            }).json()
            question_b = client.post("/interview-questions/mine", headers=headers_b, json={
                "application_id": app_b["id"], "question": "Private interview question B?",
            }).json()
            listed_b = client.get("/interview-questions/mine", headers=headers_b).json()["items"]
            assert [row["id"] for row in listed_b] == [question_b["id"]]
            assert client.put(f"/interview-questions/mine/{question_a['id']}", headers=headers_b,
                              json={"question": "Unauthorized edit?"}).status_code == 404
            assert client.delete(f"/interview-questions/mine/{question_a['id']}", headers=headers_b).status_code == 404
            assert client.post("/interview-questions/mine", headers=headers_b, json={
                "application_id": app_a["id"], "question": "Cross-owner interview question?",
            }).status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
