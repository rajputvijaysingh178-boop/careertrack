from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all model metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.application import Application, ApplicationStatusHistory
from app.models.user import User


def test_two_consecutive_application_creates_persist_and_remain_owner_scoped(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'application-round-trip.db'}")
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with testing_session() as db:
        owner = User(name="Application Owner", email="app-owner-roundtrip@example.test",
                     password_hash=hash_password("roundtrip-owner-password"))
        other = User(name="Other Owner", email="other-owner-roundtrip@example.test",
                     password_hash=hash_password("roundtrip-other-password"))
        db.add_all([owner, other])
        db.commit()
        owner_id, other_id = owner.id, other.id

    def override_db():
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    owner_headers = {"Authorization": f"Bearer {create_access_token(str(owner_id), 'USER')}"}
    other_headers = {"Authorization": f"Bearer {create_access_token(str(other_id), 'USER')}"}
    try:
        with TestClient(app) as client:
            first = client.post("/applications", headers=owner_headers, json={
                "job_title": "Backend Engineer",
                "company_name": "Northstar Labs",
                "jd_text": "Build and maintain Python services.",
                "status": "APPLIED",
            })
            second = client.post("/applications", headers=owner_headers, json={
                # A client-supplied owner must not override the authenticated user.
                "user_id": other_id,
                "job_title": "Data Engineer",
                "company_name": "Contoso Analytics",
                "jd_text": "Develop reliable batch and streaming data pipelines.",
                "status": "SAVED",
            })
            assert first.status_code == 201, first.text
            assert second.status_code == 201, second.text
            first_record, second_record = first.json(), second.json()
            assert first_record["user_id"] == second_record["user_id"] == owner_id
            assert first_record["jd_text"] == "Build and maintain Python services."
            assert second_record["jd_text"] == "Develop reliable batch and streaming data pipelines."

            owner_list = client.get("/applications?limit=200", headers=owner_headers)
            assert owner_list.status_code == 200, owner_list.text
            assert {row["id"] for row in owner_list.json()} == {first_record["id"], second_record["id"]}
            assert client.get("/applications", headers=other_headers).json() == []
            assert client.get(f"/applications/{first_record['id']}", headers=other_headers).status_code == 404

        # A new SQLAlchemy session verifies that both route commits persisted.
        with testing_session() as verification_db:
            persisted = verification_db.query(Application).filter_by(user_id=owner_id).all()
            assert {record.id for record in persisted} == {first_record["id"], second_record["id"]}
            assert all(record.user_id != other_id for record in persisted)
            histories = verification_db.query(ApplicationStatusHistory).filter(
                ApplicationStatusHistory.application_id.in_([first_record["id"], second_record["id"]])
            ).all()
            assert len(histories) == 2
            assert {entry.changed_by for entry in histories} == {owner_id}
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
