"""Authenticated AI route integration tests using isolated SQLite and mocked Gemini HTTP."""
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.company import Company
from app.models.job import Job
from app.models.skill import JobSkill, Skill
from app.models.user import User


def test_authenticated_ai_routes_use_mocked_gemini_and_return_ai_results(monkeypatch):
    monkeypatch.setattr(settings, "LLM_API_KEY", "offline-test-key")
    monkeypatch.setattr(settings, "LLM_MODEL", "gemini-3.8-flash")
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    user = User(name="AI Test User", email="ai-test@example.com",
                password_hash=hash_password("ai-test-password"), role="USER", status="ACTIVE")
    company = Company(name="AI Test Company", status="ACTIVE")
    skill = Skill(name="Python", category="Backend")
    db.add_all([user, company, skill])
    db.flush()
    job = Job(company_id=company.id, title="Python Backend Engineer",
              description="Build Python APIs using FastAPI and SQL for production services.",
              status="ACTIVE", work_mode="REMOTE", employment_type="FULL_TIME",
              job_type="Backend", experience_min=2)
    db.add(job)
    db.flush()
    db.add(JobSkill(job_id=job.id, skill_id=skill.id, importance="REQUIRED"))
    db.commit()

    def override_db():
        yield db

    def mocked_gemini(*args, **kwargs):
        request = kwargs["json"]
        prompt = request["contents"][0]["parts"][0]["text"]
        response = Mock()
        if "interview preparation plan" in prompt.lower() or '"days"' in prompt:
            text = '{"days":[{"title":"Python API design","topics":["FastAPI"],"tasks":["Build an endpoint"]}]}'
        else:
            text = '{"skills":[{"name":"Python","importance":"REQUIRED"},{"name":"Docker","importance":"PREFERRED"}],"tools":["Docker"],"responsibilities":["Build reliable APIs"]}'
        response.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]}
        response.raise_for_status.return_value = None
        return response

    from unittest.mock import patch

    app.dependency_overrides[get_db] = override_db
    try:
        with patch("app.ai.llm_client.httpx.post", side_effect=mocked_gemini) as post:
            with TestClient(app) as client:
                login = client.post("/auth/login/json", json={
                    "email": user.email, "password": "ai-test-password"
                })
                assert login.status_code == 200, login.text
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                jd = client.post("/jd-analyzer/analyze", headers=headers, json={
                    "jd_text": job.description, "use_ai": True
                })
                assert jd.status_code == 200, jd.text
                jd_result = jd.json()
                assert jd_result["ai_used"] is True, jd_result
                assert jd_result["source"] == "rules+ai"
                assert "Docker" in {item["name"] for item in jd_result["skills"]}

                plan = client.post("/prep/plan", headers=headers, json={
                    "job_id": job.id, "days": 3, "use_ai": True
                })
                assert plan.status_code == 200, plan.text
                assert plan.json()["source"] == "ai"
                assert plan.json()["plan"][0]["title"] == "Python API design"
                assert post.call_count == 2
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
