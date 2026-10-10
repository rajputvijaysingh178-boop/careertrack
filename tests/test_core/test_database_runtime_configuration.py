from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text

import app.models
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token, decode_token
from app.main import app


def test_runtime_engine_and_session_use_the_isolated_sqlite_url():
    assert settings.DATABASE_URL.startswith("sqlite:")
    assert engine.dialect.name == "sqlite"
    assert SessionLocal.kw["bind"] is engine
    with SessionLocal() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
    assert "users" in inspect(engine).get_table_names()
    assert len(Base.metadata.tables) == 22


def test_postgresql_driver_loads_without_opening_a_connection():
    pg_engine = create_engine("postgresql+psycopg://test:test@localhost/test")
    try:
        assert pg_engine.dialect.name == "postgresql"
        assert pg_engine.dialect.driver == "psycopg"
    finally:
        pg_engine.dispose()


def test_jwt_uses_configured_algorithm_and_expiry_without_exposing_token():
    token = create_access_token("config-test-user", "USER")
    payload = decode_token(token)
    expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    remaining = (expiry - datetime.now(timezone.utc)).total_seconds()
    assert payload["sub"] == "config-test-user"
    assert payload["role"] == "USER"
    assert 0 < remaining <= settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_cors_allows_configured_origins_and_rejects_unconfigured_origins():
    from fastapi.testclient import TestClient

    allowed = settings.cors_list[0]
    with TestClient(app) as client:
        response = client.get("/", headers={"Origin": allowed})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == allowed

        rejected = client.get("/", headers={"Origin": "https://unconfigured.example"})
        assert rejected.status_code == 200
        assert "access-control-allow-origin" not in rejected.headers
