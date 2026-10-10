from sqlalchemy import create_engine, inspect
import pytest

from scripts.migrate_m2_schema import upgrade


def test_m2_upgrade_adds_columns_to_empty_placeholder_tables():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        for table in ("applications", "interviews", "bookmarks", "notes", "documents", "reminders"):
            connection.exec_driver_sql(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')

    changes = upgrade(engine)
    columns = {col["name"] for col in inspect(engine).get_columns("applications")}
    assert "user_id" in columns
    assert "jd_text" in columns
    assert "job_title" in columns
    assert any(item.startswith("interviews.") for item in changes)
    assert "application_status_history" in inspect(engine).get_table_names()
    assert {"application_events", "hr_calls"}.issubset(inspect(engine).get_table_names())
    engine.dispose()


def test_m2_upgrade_refuses_nonempty_placeholder_without_partial_ddl():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE applications (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO applications (id) VALUES (1)')
    with pytest.raises(RuntimeError, match="non-empty legacy table applications"):
        upgrade(engine)
    assert "application_status_history" not in inspect(engine).get_table_names()
    engine.dispose()


def test_m2_upgrade_adds_nullable_interview_history_snapshots_without_losing_rows():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql('''CREATE TABLE interview_status_history (
            id INTEGER PRIMARY KEY, interview_id INTEGER NOT NULL, old_status VARCHAR(32),
            new_status VARCHAR(32) NOT NULL, changed_at DATETIME NOT NULL, feedback TEXT
        )''')
        connection.exec_driver_sql('''INSERT INTO interview_status_history
            (id, interview_id, old_status, new_status, changed_at, feedback)
            VALUES (1, 7, 'SCHEDULED', 'COMPLETED', '2026-01-01 12:00:00', 'Completed round')''')

    changes = upgrade(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("interview_status_history")}
    assert {"round_name", "scheduled_at", "mode", "interviewer", "meeting_link"}.issubset(columns)
    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            "SELECT interview_id, new_status, feedback FROM interview_status_history WHERE id = 1"
        ).one()
    assert tuple(row) == (7, "COMPLETED", "Completed round")
    assert "interview_status_history.round_name" in changes
    engine.dispose()
