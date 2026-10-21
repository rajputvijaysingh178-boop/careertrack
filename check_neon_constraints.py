
from sqlalchemy import inspect
from app.core.database import engine

try:
    inspector = inspect(engine)

    for table in inspector.get_table_names():
        print(f"\nTABLE: {table}")

        for fk in inspector.get_foreign_keys(table):
            print(
                "  FOREIGN KEY:",
                fk["constrained_columns"],
                "->",
                fk["referred_table"],
                fk["referred_columns"],
            )

        for unique in inspector.get_unique_constraints(table):
            print("  UNIQUE:", unique["name"], unique["column_names"])

finally:
    engine.dispose()
