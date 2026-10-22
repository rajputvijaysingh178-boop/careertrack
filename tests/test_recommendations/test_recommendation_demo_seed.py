import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.database import Base
from app.models.user import User
from app.services.recommendation_service import RecommendationService
from scripts.seed_recommendation_demo import (
    CONFIRMED_TEST_HOST,
    guarded_test_database_url,
    seed_demo_jobs,
)


def test_test_database_guard_requires_exact_host_and_explicit_acknowledgement():
    url = f"postgresql+psycopg://unit:unit@{CONFIRMED_TEST_HOST}/careertrack"
    with pytest.raises(RuntimeError, match="CAREERTRACK_TEST_DATABASE_URL"):
        guarded_test_database_url({})
    with pytest.raises(RuntimeError, match="EXPECTED_TEST_HOST"):
        guarded_test_database_url({"CAREERTRACK_TEST_DATABASE_URL": url})
    with pytest.raises(RuntimeError, match="confirmed test target"):
        guarded_test_database_url({
            "CAREERTRACK_TEST_DATABASE_URL": url.replace(CONFIRMED_TEST_HOST, "production.invalid"),
            "CAREERTRACK_EXPECTED_TEST_HOST": CONFIRMED_TEST_HOST,
        })
    assert guarded_test_database_url({
        "CAREERTRACK_TEST_DATABASE_URL": url,
        "CAREERTRACK_EXPECTED_TEST_HOST": CONFIRMED_TEST_HOST,
    }) == url


def test_demo_seed_is_read_only_in_dry_run_and_idempotent_when_applied():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        user = User(name="Recommendation Test", email="recommendation-seed@example.test",
                    password_hash="test", role="USER", status="ACTIVE")
        db.add(user)
        db.commit()

        empty = RecommendationService(db).recommend_jobs(user.id)
        assert empty["jobs"] == []
        assert "No active or unexpired jobs" in empty["note"]

        planned = seed_demo_jobs(db, apply=False)
        assert planned == {
            "company_to_create": 1,
            "skills_to_create": 5,
            "jobs_to_create": 3,
            "job_skill_links_to_create": 8,
        }
        assert db.query(app.models.Company).count() == 0
        assert db.query(app.models.Job).count() == 0
        assert db.query(app.models.Skill).count() == 0

        applied = seed_demo_jobs(db, apply=True)
        db.commit()
        assert applied == planned
        saved = RecommendationService(db).set_my_skills(user.id, ["Python", "React"])
        assert saved["unknown"] == []
        assert set(saved["skills"]) == {"Python", "React"}
        suggestions = RecommendationService(db).recommend_jobs(user.id)
        assert len(suggestions["jobs"]) == 3
        assert all(item["match_percent"] > 0 for item in suggestions["jobs"])

        repeated = seed_demo_jobs(db, apply=True)
        db.commit()
        assert repeated == {
            "company_to_create": 0,
            "skills_to_create": 0,
            "jobs_to_create": 0,
            "job_skill_links_to_create": 0,
        }
        assert db.query(app.models.Job).count() == 3
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_unknown_skill_submission_does_not_erase_existing_profile():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        user = User(name="Recommendation Profile Test", email="recommendation-profile@example.test",
                    password_hash="test", role="USER", status="ACTIVE")
        db.add(user)
        db.commit()
        seed_demo_jobs(db, apply=True)
        service = RecommendationService(db)

        first = service.set_my_skills(user.id, ["Python", "React"])
        assert set(first["skills"]) == {"Python", "React"}

        rejected = service.set_my_skills(user.id, ["Unlisted Specialty Skill"])
        assert rejected["unknown"] == ["Unlisted Specialty Skill"]
        assert set(rejected["skills"]) == {"Python", "React"}
        assert set(service.my_skills(user.id)) == {"Python", "React"}

        cleared = service.set_my_skills(user.id, [])
        assert cleared == {"skills": [], "unknown": []}
        assert service.my_skills(user.id) == []
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_unavailable_skill_catalog_does_not_clear_profile(monkeypatch):
    from fastapi import HTTPException
    from app.repositories.prep_lookup_repository import PrepLookupRepository

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        user = User(name="Catalog Failure Test", email="catalog-failure@example.test",
                    password_hash="test", role="USER", status="ACTIVE")
        db.add(user)
        db.commit()
        seed_demo_jobs(db, apply=True)
        service = RecommendationService(db)
        service.set_my_skills(user.id, ["Python"])

        monkeypatch.setattr(PrepLookupRepository, "list_skills", lambda self: [])
        with pytest.raises(HTTPException) as error:
            service.set_my_skills(user.id, ["React"])
        assert error.value.status_code == 503
        assert service.my_skills(user.id) == ["Python"]
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
