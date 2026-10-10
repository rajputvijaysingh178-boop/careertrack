"""OWNER: M2 - additive schema upgrade from the original placeholder tables.

Run with `python -m scripts.migrate_m2_schema --apply` against a local SQLite DB.
Remote databases require an explicit `--allow-remote` flag. This migration never
drops tables or columns and refuses to alter non-empty legacy M2 tables because
their owner/status data cannot be inferred safely.
"""
import argparse

from sqlalchemy import Engine, inspect, text

import app.models  # noqa: F401 - register metadata
from app.core.config import settings
from app.core.database import Base
from app.models.application import Application, ApplicationStatusHistory
from app.models.application_event import ApplicationEvent, HRCall
from app.models.bookmark import Bookmark
from app.models.document import Document
from app.models.interview import Interview, InterviewStatusHistory
from app.models.note import Note
from app.models.reminder import Reminder

TRACKER_MODELS = [Application, ApplicationStatusHistory, ApplicationEvent, HRCall, Bookmark, Interview, InterviewStatusHistory,
                  Note, Document, Reminder]
SAFE_EXISTING_ADDITIONS = {
    "interview_status_history": {
        "round_name", "scheduled_at", "mode", "interviewer", "meeting_link",
    }
}


def upgrade(engine: Engine) -> list[str]:
    """Create missing M2 tables and add missing columns to empty placeholder tables."""
    inspector = inspect(engine)
    # Audit every existing tracker table before performing any DDL, so a refusal
    # never leaves a partly upgraded schema behind.
    with engine.connect() as connection:
        for model in TRACKER_MODELS:
            table = model.__tablename__
            if table not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            missing = {column.name for column in model.__table__.columns} - existing
            if missing:
                safe = SAFE_EXISTING_ADDITIONS.get(table, set())
                unsafe_missing = missing - safe
                count = connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
                if count and unsafe_missing:
                    raise RuntimeError(f"Refusing to migrate non-empty legacy table {table}; map records first")

    Base.metadata.create_all(bind=engine)
    changes = []
    inspector = inspect(engine)
    with engine.begin() as connection:
        for model in TRACKER_MODELS:
            table = model.__tablename__
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column in model.__table__.columns:
                if column.name in existing:
                    continue
                sql_type = column.type.compile(dialect=engine.dialect)
                nullable = " NULL" if column.nullable else " NOT NULL"
                default = ""
                if column.server_default is not None:
                    default = f" DEFAULT {column.server_default.arg}"
                connection.exec_driver_sql(
                    f'ALTER TABLE "{table}" ADD COLUMN "{column.name}" {sql_type}{nullable}{default}')
                changes.append(f"{table}.{column.name}")
            # Refresh this table's column inventory before processing its indexes.
            inspector = inspect(connection)
            for index in model.__table__.indexes:
                index.create(bind=connection, checkfirst=True)
    return changes


def main():
    parser = argparse.ArgumentParser(description="Safely upgrade CareerTrack's placeholder M2 tables")
    parser.add_argument("--apply", action="store_true", help="apply the additive migration")
    parser.add_argument("--allow-remote", action="store_true", help="allow a non-SQLite database")
    args = parser.parse_args()
    if not args.apply:
        parser.error("No changes made. Re-run with --apply after reviewing the target DATABASE_URL.")
    if not settings.DATABASE_URL.startswith("sqlite") and not args.allow_remote:
        parser.error("Remote database detected. Use --allow-remote only after verifying a backup and target.")
    from sqlalchemy import create_engine
    connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(settings.sqlalchemy_database_url, connect_args=connect_args,
                           pool_pre_ping=not settings.DATABASE_URL.startswith("sqlite"))
    try:
        changes = upgrade(engine)
    finally:
        engine.dispose()
    print("M2 schema is up to date." if not changes else "Added columns: " + ", ".join(changes))


if __name__ == "__main__":
    main()
