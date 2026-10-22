from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


def test_admin_can_assign_application_to_selected_user_without_sharing_it():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    admin = User(name="Admin", email="admin-assignment@example.test", password_hash=hash_password("test-password"), role="ADMIN")
    owner = User(name="Intended owner", email="owner-assignment@example.test", password_hash=hash_password("test-password"))
    other = User(name="Other user", email="other-assignment@example.test", password_hash=hash_password("test-password"))
    db.add_all([admin, owner, other])
    db.commit()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    headers = {
        "admin": {"Authorization": f"Bearer {create_access_token(str(admin.id), 'ADMIN')}"},
        "owner": {"Authorization": f"Bearer {create_access_token(str(owner.id), 'USER')}"},
        "other": {"Authorization": f"Bearer {create_access_token(str(other.id), 'USER')}"},
    }
    try:
        with TestClient(app) as client:
            created = client.post("/admin/applications", headers=headers["admin"], json={
                "user_id": owner.id,
                "job_title": "Senior Data Analyst",
                "company_name": "Northstar Labs",
                "jd_text": "Analyze product metrics and communicate findings to business teams.",
                "status": "APPLIED",
            })
            assert created.status_code == 201, created.text
            record = created.json()
            assert record["user_id"] == owner.id
            assert record["jd_text"].startswith("Analyze product metrics")

            visible_to_owner = client.get("/applications", headers=headers["owner"])
            assert visible_to_owner.status_code == 200
            assert [item["id"] for item in visible_to_owner.json()] == [record["id"]]
            assert client.get("/applications", headers=headers["other"]).json() == []
            assert client.get("/applications", headers=headers["admin"]).json() == []
            assert client.post("/admin/applications", headers=headers["owner"], json={
                "user_id": other.id, "job_title": "Unauthorized target",
            }).status_code == 403
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
