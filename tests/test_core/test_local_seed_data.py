from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import Application, Blog, Company, Document, Interview, InterviewQuestion, Job, Material, Note, Reminder, User
from scripts.seed_local_test_data import ADMIN_EMAIL, ADMIN_PASSWORD, USERS, seed_data


def test_local_test_seed_is_idempotent_and_relationships_are_complete(tmp_path):
    db_path = tmp_path / "careertrack-seed-test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    try:
        first = seed_data(engine)
        second = seed_data(engine)
        assert second == first
        assert first["companies"] == 2
        assert first["jobs"] == 2
        assert first["users"] == 3
        assert first["applications"] == 4
        assert first["interviews"] == first["notes"] == first["reminders"] == 2
        assert first["bookmarks"] == first["documents"] == 2
        assert first["interview_questions"] == first["materials"] == first["blogs"] == 2
        assert first["job_skills"] >= 8
        assert first["user_skills"] >= 4

        Session = sessionmaker(bind=engine)
        with Session() as db:
            jobs = db.query(Job).order_by(Job.id).all()
            admin = db.query(User).filter_by(role="ADMIN").one()
            users = db.query(User).filter_by(role="USER").all()
            assert len(users) == 2
            assert all(job.status == "ACTIVE" and job.created_by == admin.id for job in jobs)
            assert all(job.company_id and job.description and job.application_url for job in jobs)
            for user in users:
                applications = db.query(Application).filter_by(user_id=user.id).all()
                assert len(applications) == 2
                assert len({app.status for app in applications}) == 2
                for application in applications:
                    job = db.get(Job, application.job_id)
                    assert application.jd_text == job.description
                    assert application.company_id == job.company_id
            assert db.query(Company).count() == 2
            assert db.query(Interview).count() == 2
            assert db.query(Note).count() == 2
            assert db.query(Reminder).count() == 2
            assert db.query(Document).count() == 2
            assert db.query(InterviewQuestion).count() == 2
            assert db.query(Material).count() == 2
            assert db.query(Blog).filter_by(status="PUBLISHED").count() == 2
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_seeded_admin_content_is_public_and_private_records_stay_owned(tmp_path):
    db_path = tmp_path / "careertrack-api-seed-test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    seed_data(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as db:
        admin = db.query(User).filter_by(email=ADMIN_EMAIL).one()
        users = {user.email: user for user in db.query(User).filter_by(role="USER").all()}
        user_apps = {
            email: db.query(Application).filter_by(user_id=user.id).order_by(Application.id).all()
            for email, user in users.items()
        }
        private_ids = {
            "note": {row.user_id: row.id for row in db.query(Note).all()},
            "document": {row.user_id: row.id for row in db.query(Document).all()},
            "interview": {row.application_id: row.id for row in db.query(Interview).all()},
        }

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    admin_headers = {"Authorization": f"Bearer {create_access_token(str(admin.id), admin.role)}"}
    tokens = {
        email: {"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}
        for email, user in users.items()
    }
    try:
        with TestClient(app) as client:
            admin_login = client.post("/auth/login/json", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
            })
            assert admin_login.status_code == 200, admin_login.text
            admin_me = client.get("/auth/me", headers={
                "Authorization": f"Bearer {admin_login.json()['access_token']}"})
            assert admin_me.json()["role"] == "ADMIN"
            for email, _name, password, _location in USERS:
                login = client.post("/auth/login/json", json={"email": email, "password": password})
                assert login.status_code == 200
                me = client.get("/auth/me", headers={
                    "Authorization": f"Bearer {login.json()['access_token']}"})
                assert me.json()["role"] == "USER"

            # Admin-created, active/published catalog content is visible to both users.
            for email in users:
                headers = tokens[email]
                jobs = client.get("/jobs", headers=headers)
                assert jobs.status_code == 200
                assert jobs.json()["total"] == 2
                assert all(row["status"] == "ACTIVE" for row in jobs.json()["items"])
                assert client.get("/blogs", headers=headers).json()["total"] == 2
                assert client.get("/materials", headers=headers).json()["total"] == 2
                assert client.get("/interview-questions", headers=headers).json()["total"] == 2
                assert client.get("/admin/dashboard", headers=headers).status_code == 403

                own_applications = client.get("/applications", headers=headers)
                assert own_applications.status_code == 200
                assert len(own_applications.json()) == 2
                assert len({row["status"] for row in own_applications.json()}) == 2
                assert len(client.get("/notes", headers=headers).json()) == 1
                assert len(client.get("/reminders", headers=headers).json()) == 1
                assert len(client.get("/documents", headers=headers).json()) == 1
                assert len(client.get("/bookmarks", headers=headers).json()) == 1
                assert client.get("/interview-questions/mine", headers=headers).json()["total"] == 1
                assert len(client.get("/resume-match/history", headers=headers).json()) == 1

            emails = list(users)
            first_email, second_email = emails[0], emails[1]
            first_user, second_user = users[first_email], users[second_email]
            first_app = user_apps[first_email][0]
            second_app = user_apps[second_email][0]

            assert client.get(f"/applications/{first_app.id}", headers=tokens[second_email]).status_code == 404
            assert client.get(f"/interviews/applications/{first_app.id}",
                              headers=tokens[second_email]).status_code == 404
            assert client.delete(f"/documents/{private_ids['document'][first_user.id]}",
                                 headers=tokens[second_email]).status_code == 404
            assert client.put(f"/notes/{private_ids['note'][first_user.id]}",
                              headers=tokens[second_email],
                              json={"title": "Unauthorized update"}).status_code == 404
            assert client.get("/interview-questions/mine", headers=tokens[second_email]).json()["total"] == 1
            assert first_app.user_id != second_user.id and second_app.user_id == second_user.id

            # The seeded admin can read all test applications; users remain USER role.
            assert len(client.get("/applications", headers=admin_headers).json()) == 0
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_seed_target_path_guard_rejects_database_outside_test_directory():
    from scripts.seed_local_test_data import _safe_database_path

    try:
        _safe_database_path("careertrack.db")
    except RuntimeError as exc:
        assert "inside the backend .testdata directory" in str(exc)
    else:
        raise AssertionError("Seeder accepted a database path outside its isolated test directory")
