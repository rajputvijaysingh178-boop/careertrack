
from sqlalchemy import inspect
from app.core.database import engine

tables = [
    "users",
    "jobs",
    "companies",
    "applications",
    "bookmarks",
    "interviews",
    "notes",
    "documents",
    "reminders",
]

try:
    inspector = inspect(engine)

    for table in tables:
        if table not in inspector.get_table_names():
            print(f"\n{table}: TABLE MISSING")
            continue

        print(f"\nTABLE: {table}")
        for column in inspector.get_columns(table):
            print(
                f"  {column['name']}: "
                f"{column['type']}, "
                f"nullable={column['nullable']}, "
                f"primary_key={column['name'] in inspector.get_pk_constraint(table)['constrained_columns']}"
            )
finally:
    engine.dispose()

