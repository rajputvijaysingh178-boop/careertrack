
from sqlalchemy import inspect, text
from app.core.database import engine

tables_to_check = [
    "applications",
    "reminders",
    "interviews",
    "application_events",
    "application_status_history",
    "hr_calls",
    "interview_status_history",
    "bookmarks",
    "notes",
    "documents",
]

try:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.connect() as connection:
        for table in tables_to_check:
            if table not in existing_tables:
                print(f"{table}: TABLE MISSING")
                continue

            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()

            print(f"{table}: {count} rows")
finally:
    engine.dispose()
