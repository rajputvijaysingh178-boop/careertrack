import pytest
from sqlalchemy import Column, Float, String, create_engine, inspect, text
from sqlalchemy.dialects import postgresql

from scripts.migrate_m2_schema import (
    _requires_remote_apply_ack,
    database_target,
    plan,
    select_database_url,
    upgrade,
    validate_expected_test_host,
    _type_matches,
)


@pytest.fixture
def engine():
    db = create_engine("sqlite://")
    with db.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE jobs (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE companies (id INTEGER PRIMARY KEY)"))
        # An unrelated legacy table stands in for M1/M3 and must be untouched.
        conn.execute(text("CREATE TABLE m1_data (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)"))
        conn.execute(text("INSERT INTO m1_data VALUES (1, 'keep')"))
    yield db
    db.dispose()


def test_plan_reports_missing_m2_and_leaves_unrelated_tables_alone(engine):
    result = plan(engine)
    assert "CREATE TABLE: applications" in result
    assert "CREATE TABLE: hr_calls" in result
    assert "CREATE TABLE: interview_status_history" in result
    assert not any("m1_data" in item for item in result)
    assert inspect(engine).get_table_names() == ["companies", "jobs", "m1_data", "users"]


def test_upgrade_creates_only_m2_tables_and_preserves_unrelated_data(engine):
    upgrade(engine)
    inspector = inspect(engine)
    expected = {"applications", "application_status_history", "application_events", "hr_calls",
                "bookmarks", "interviews", "interview_status_history", "notes", "documents", "reminders"}
    assert expected.issubset(set(inspector.get_table_names()))
    assert "user_id" in {c["name"] for c in inspector.get_columns("reminders")}
    application_indexes = inspector.get_indexes("applications")
    assert not any(index["column_names"] == ["id"] for index in application_indexes)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT payload FROM m1_data WHERE id=1")).scalar_one() == "keep"


def test_nonempty_legacy_table_with_required_missing_column_is_refused(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE reminders (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO reminders VALUES (1)"))
    with pytest.raises(RuntimeError, match="non-empty and required column"):
        upgrade(engine)
    assert "reminders" in inspect(engine).get_table_names()
    assert {c["name"] for c in inspect(engine).get_columns("reminders")} == {"id"}


def test_duplicate_bookmarks_block_unique_constraint_repair(engine):
    upgrade(engine)
    with engine.begin() as conn:
        # SQLite cannot add constraints, so validate duplicate detection through plan
        conn.execute(text("DROP TABLE bookmarks"))
        conn.execute(text("CREATE TABLE bookmarks (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, job_id INTEGER NOT NULL, type VARCHAR(16) NOT NULL, created_at DATETIME NOT NULL)"))
        conn.execute(text("INSERT INTO bookmarks VALUES (1, 1, 1, 'SAVE', '2026-01-01')"))
        conn.execute(text("INSERT INTO bookmarks VALUES (2, 1, 1, 'SAVE', '2026-01-02')"))
    with pytest.raises(RuntimeError, match="duplicate values"):
        plan(engine)


def test_plan_reports_missing_bookmark_unique_constraint(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE bookmarks (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL, type VARCHAR(16) NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
    actions = plan(engine)
    assert "ADD UNIQUE: uq_bookmark_user_job" in actions


def test_plan_recognizes_existing_bookmark_unique_constraint(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE bookmarks (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL, type VARCHAR(16) NOT NULL,
                created_at DATETIME NOT NULL,
                CONSTRAINT uq_bookmark_user_job UNIQUE (user_id, job_id)
            )
        """))
    actions = plan(engine)
    assert "ADD UNIQUE: uq_bookmark_user_job" not in actions


def test_plan_does_not_check_unique_values_until_columns_exist(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE bookmarks (id INTEGER PRIMARY KEY)"))
    actions = plan(engine)
    assert "ADD COLUMN: bookmarks.user_id" in actions
    assert "ADD COLUMN: bookmarks.job_id" in actions


def test_remote_apply_requires_explicit_acknowledgement_but_sqlite_does_not():
    assert _requires_remote_apply_ack(
        "postgresql+psycopg://example", apply=True, allow_remote=False
    )
    assert not _requires_remote_apply_ack(
        "postgresql+psycopg://example", apply=True, allow_remote=True
    )
    assert not _requires_remote_apply_ack(
        "sqlite:///isolated-test.db", apply=True, allow_remote=False
    )
    assert not _requires_remote_apply_ack(
        "postgresql+psycopg://example", apply=False, allow_remote=False
    )


def test_dry_run_selects_explicit_test_url_without_using_configured_url():
    assert select_database_url(
        dry_run=True,
        test_database_url="sqlite:///isolated-test.db",
    ) == "sqlite:///isolated-test.db"


def test_dry_run_fails_closed_when_test_url_is_missing():
    with pytest.raises(ValueError, match="CAREERTRACK_TEST_DATABASE_URL"):
        select_database_url(
            dry_run=True,
            test_database_url=None,
        )


def test_plan_does_not_propose_primary_key_index_as_redundant(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE applications (id INTEGER PRIMARY KEY)"))
    actions = plan(engine)
    assert "ADD INDEX: ix_applications_id" not in actions
    assert "ADD INDEX: ix_applications_user_id" in actions


def test_database_target_reports_host_and_database_without_credentials():
    host, database = database_target(
        "postgresql+psycopg://example_user:secret_value@db.example.test:5432/careertrack"
    )
    assert host == "db.example.test"
    assert database == "careertrack"
    assert "secret_value" not in host
    assert "secret_value" not in database


def test_postgresql_float_and_double_precision_are_compatible():
    column = Column("salary_expectation", Float())
    assert _type_matches(
        column,
        postgresql.DOUBLE_PRECISION(),
        postgresql.dialect(),
    )


def test_type_match_still_rejects_genuinely_incompatible_types():
    column = Column("salary_expectation", Float())
    assert not _type_matches(
        column,
        String(100),
        postgresql.dialect(),
    )


def test_type_match_does_not_accept_precision_qualified_float_aliases():
    column = Column("salary_expectation", Float())
    assert not _type_matches(
        column,
        postgresql.FLOAT(precision=24),
        postgresql.dialect(),
    )


def test_apply_uses_test_url_exclusively_even_when_remote():
    assert select_database_url(
        dry_run=False,
        test_database_url="postgresql+psycopg://user:secret@test-branch.example/db",
    ) == "postgresql+psycopg://user:secret@test-branch.example/db"


def test_apply_fails_closed_without_test_url():
    with pytest.raises(ValueError, match="--apply requires CAREERTRACK_TEST_DATABASE_URL"):
        select_database_url(
            dry_run=False,
            test_database_url=None,
        )


def test_apply_requires_expected_hostname():
    url = "postgresql+psycopg://user:secret@test-branch.example/db"
    with pytest.raises(ValueError, match="CAREERTRACK_EXPECTED_TEST_HOST"):
        validate_expected_test_host(url, None)


def test_apply_rejects_hostname_mismatch():
    url = "postgresql+psycopg://user:secret@test-branch.example/db"
    with pytest.raises(ValueError, match="does not match"):
        validate_expected_test_host(url, "production.example")


def test_apply_accepts_expected_test_hostname_without_exposing_credentials():
    url = "postgresql+psycopg://user:secret@test-branch.example/db"
    validate_expected_test_host(url, "TEST-BRANCH.EXAMPLE.")


def test_main_dry_run_missing_test_url_stops_before_connecting(monkeypatch):
    import sys

    from scripts.migrate_m2_schema import main

    monkeypatch.delenv("CAREERTRACK_TEST_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["migrate_m2_schema", "--dry-run"])
    with pytest.raises(SystemExit):
        main()


def test_main_dry_run_requires_expected_host_before_connecting(monkeypatch):
    import sys

    import sqlalchemy
    from scripts.migrate_m2_schema import main

    monkeypatch.setenv(
        "CAREERTRACK_TEST_DATABASE_URL",
        "postgresql+psycopg://user:secret@test-branch.example/db",
    )
    monkeypatch.delenv("CAREERTRACK_EXPECTED_TEST_HOST", raising=False)
    monkeypatch.setattr(sys, "argv", ["migrate_m2_schema", "--dry-run"])
    monkeypatch.setattr(
        sqlalchemy,
        "create_engine",
        lambda *args, **kwargs: pytest.fail("engine must not be created before host validation"),
    )
    with pytest.raises(SystemExit):
        main()
