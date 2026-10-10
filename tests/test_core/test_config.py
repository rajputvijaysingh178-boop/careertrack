import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_accept_legacy_jwt_secret_and_normalize_neon_url():
    settings = Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db?sslmode=require",
                        JWT_SECRET="s" * 40, CORS_ORIGINS="https://app.example, https://admin.example/")
    assert settings.SECRET_KEY == "s" * 40
    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")
    assert settings.cors_list == ["https://app.example", "https://admin.example"]


def test_postgres_settings_reject_missing_or_short_jwt_secret():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db", SECRET_KEY="short")
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db",
                 SECRET_KEY="CHANGE_ME_USE_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS")


def test_sqlite_development_settings_keep_local_default():
    settings = Settings(_env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="local-test-secret")
    assert settings.sqlalchemy_database_url == "sqlite://"
    assert settings.should_auto_create_schema is True


def test_postgres_startup_does_not_implicitly_change_schema():
    settings = Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db",
                        SECRET_KEY="s" * 40)
    assert settings.should_auto_create_schema is False
    explicit = Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db",
                        SECRET_KEY="s" * 40, AUTO_CREATE_SCHEMA=True)
    assert explicit.should_auto_create_schema is True


def test_postgres_admin_bootstrap_rejects_example_password():
    with pytest.raises(ValidationError, match="ADMIN_PASSWORD"):
        Settings(_env_file=None, DATABASE_URL="postgresql://user:pass@host.example/db",
                 SECRET_KEY="s" * 40, ADMIN_EMAIL="admin@example.com",
                 ADMIN_PASSWORD="CHANGE_ME_USE_A_UNIQUE_STRONG_PASSWORD")
