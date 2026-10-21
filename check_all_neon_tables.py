
from sqlalchemy import inspect, text
from app.core.database import engine

try:
    with engine.connect() as connection:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("Neon tables and row counts:\n")

        for table in tables:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()

            print(f"{table}: {count} rows")

finally:
    engine.dispose()
