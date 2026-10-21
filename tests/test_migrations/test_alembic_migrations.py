from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from app.core.config import Settings
from app.core.database import Base
from scripts.seed_demo import require_local_sqlite

ROOT = Path(__file__).resolve().parents[2]
INI = ROOT / "alembic.ini"


def _config(output_buffer=None):
    return Config(str(INI), output_buffer=output_buffer)


def test_initial_revision_upgrades_an_isolated_sqlite_database(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration-test.db'}"
    monkeypatch.setenv("CAREERTRACK_ALEMBIC_DATABASE_URL", database_url)
    monkeypatch.delenv("CAREERTRACK_ALEMBIC_EXPECTED_HOST", raising=False)

    command.upgrade(_config(), "head")

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert set(Base.metadata.tables).issubset(inspector.get_table_names())
        assert len(Base.metadata.tables) == 22
        assert inspector.get_table_names().count("alembic_version") == 1

        bookmark_uniques = inspector.get_unique_constraints("bookmarks")
        assert any(
            item["name"] == "uq_bookmark_user_job"
            and item["column_names"] == ["user_id", "job_id"]
            for item in bookmark_uniques
        )
        application_fks = inspector.get_foreign_keys("applications")
        assert any(
            fk["constrained_columns"] == ["user_id"]
            and fk["options"].get("ondelete") == "CASCADE"
            for fk in application_fks
        )

        for table in Base.metadata.sorted_tables:
            reflected_columns = {
                column["name"]: column for column in inspector.get_columns(table.name)
            }
            primary_key = tuple(column.name for column in table.primary_key.columns)
            assert set(reflected_columns) == {column.name for column in table.columns}
            for column in table.columns:
                reflected = reflected_columns[column.name]
                assert reflected["type"].compile(dialect=engine.dialect) == column.type.compile(
                    dialect=engine.dialect
                )
                if column.name not in primary_key:
                    assert reflected["nullable"] is column.nullable
                assert reflected["default"] is None

            expected_foreign_keys = {
                (
                    tuple(element.parent.name for element in foreign_key.elements),
                    foreign_key.elements[0].column.table.name,
                    tuple(element.column.name for element in foreign_key.elements),
                    (foreign_key.ondelete or "NO ACTION").upper(),
                )
                for foreign_key in table.foreign_key_constraints
            }
            actual_foreign_keys = {
                (
                    tuple(foreign_key["constrained_columns"]),
                    foreign_key["referred_table"],
                    tuple(foreign_key["referred_columns"]),
                    (foreign_key.get("options", {}).get("ondelete") or "NO ACTION").upper(),
                )
                for foreign_key in inspector.get_foreign_keys(table.name)
            }
            assert actual_foreign_keys == expected_foreign_keys, table.name

            actual_indexes = {
                tuple(index["column_names"])
                for index in inspector.get_indexes(table.name)
            }
            for index in table.indexes:
                columns = tuple(column.name for column in index.columns)
                if columns == primary_key:
                    continue  # the PK's unique index already provides this lookup
                assert columns in actual_indexes, (table.name, index.name)
            actual_unique = {
                tuple(constraint["column_names"])
                for constraint in inspector.get_unique_constraints(table.name)
            }
            actual_unique.update(
                tuple(index["column_names"])
                for index in inspector.get_indexes(table.name)
                if index.get("unique")
            )
            for constraint in table.constraints:
                if constraint.__class__.__name__ == "UniqueConstraint":
                    assert tuple(column.name for column in constraint.columns) in actual_unique
        assert ("id",) not in {
            tuple(index["column_names"])
            for index in inspector.get_indexes("users")
        }
    finally:
        engine.dispose()


def test_postgresql_offline_sql_is_generated_without_connecting_or_dropping(monkeypatch):
    output = StringIO()
    config = _config(output)
    # Deliberately unreachable test hostname: offline mode must not open a connection.
    monkeypatch.setenv(
        "CAREERTRACK_ALEMBIC_DATABASE_URL",
        "postgresql+psycopg://offline:offline@migration-test.invalid/careertrack"
    )
    monkeypatch.setenv("CAREERTRACK_ALEMBIC_EXPECTED_HOST", "migration-test.invalid")
    command.upgrade(config, "head", sql=True)

    sql = output.getvalue().upper()
    assert "CREATE TABLE USERS" in sql
    assert "CREATE TABLE APPLICATIONS" in sql
    assert "UQ_BOOKMARK_USER_JOB" in sql
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql
    assert "DROP TABLE" not in sql
    assert "DROP COLUMN" not in sql


def test_alembic_requires_explicit_url_and_never_uses_application_database(tmp_path, monkeypatch):
    monkeypatch.delenv("CAREERTRACK_ALEMBIC_DATABASE_URL", raising=False)
    monkeypatch.delenv("CAREERTRACK_ALEMBIC_EXPECTED_HOST", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'application.db'}")

    with pytest.raises(RuntimeError, match="will not fall back to DATABASE_URL"):
        command.upgrade(_config(), "head")


@pytest.mark.parametrize(
    ("expected_host", "message"),
    [(None, "CAREERTRACK_ALEMBIC_EXPECTED_HOST"), ("other.invalid", "does not match")],
)
def test_remote_target_requires_matching_expected_host_before_connection(
    expected_host, message, monkeypatch
):
    monkeypatch.setenv(
        "CAREERTRACK_ALEMBIC_DATABASE_URL",
        "postgresql+psycopg://offline:offline@migration-test.invalid/careertrack",
    )
    if expected_host is None:
        monkeypatch.delenv("CAREERTRACK_ALEMBIC_EXPECTED_HOST", raising=False)
    else:
        monkeypatch.setenv("CAREERTRACK_ALEMBIC_EXPECTED_HOST", expected_host)

    with pytest.raises(RuntimeError, match=message):
        command.upgrade(_config(), "head")


def test_postgresql_schema_creation_is_disabled_even_when_override_is_true():
    settings = Settings(
        DATABASE_URL="postgresql+psycopg://user:password@db.invalid/careertrack",
        SECRET_KEY="test-secret-key-long-enough-for-unit-tests",
        AUTO_CREATE_SCHEMA=True,
    )
    assert settings.should_auto_create_schema is False


def test_legacy_demo_schema_helper_refuses_non_sqlite_targets():
    with pytest.raises(RuntimeError, match="restricted to local SQLite"):
        require_local_sqlite(SimpleNamespace(dialect=SimpleNamespace(name="postgresql")))
    require_local_sqlite(SimpleNamespace(dialect=SimpleNamespace(name="sqlite")))
