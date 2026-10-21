from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register model metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


def test_public_registration_cannot_assign_admin_and_auth_rejects_blocked_users():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session()
    blocked = User(
        name="Blocked User", email="blocked-auth@example.com",
        password_hash=hash_password("blocked-account-password"), role="USER", status="BLOCKED",
    )
    db.add(blocked)
    db.commit()
    blocked_id = blocked.id

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            registered = client.post("/auth/register", json={
                "name": "Public User", "email": "public-auth@example.com",
                "password": "public-account-password", "role": "ADMIN",
            })
            assert registered.status_code == 201
            assert registered.json()["role"] == "USER"
            assert registered.json()["status"] == "ACTIVE"

            login = client.post("/auth/login/json", json={
                "email": "PUBLIC-AUTH@EXAMPLE.COM", "password": "public-account-password",
            })
            assert login.status_code == 200
            token = login.json()["access_token"]
            assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200

            wrong_password = client.post("/auth/login/json", json={
                "email": "public-auth@example.com", "password": "incorrect-password",
            })
            assert wrong_password.status_code == 401

            blocked_login = client.post("/auth/login/json", json={
                "email": "blocked-auth@example.com", "password": "blocked-account-password",
            })
            assert blocked_login.status_code == 403
            blocked_token = create_access_token(str(blocked_id), "USER")
            assert client.get(
                "/auth/me", headers={"Authorization": f"Bearer {blocked_token}"}
            ).status_code == 403

            assert client.get("/auth/me").status_code == 401
            assert client.get("/auth/me", headers={"Authorization": "Bearer malformed"}).status_code == 401
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
