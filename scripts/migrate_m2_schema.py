"""Cautious, transactional schema repair for the M2 application tracker.

Run explicitly with ``python -m scripts.migrate_m2_schema --dry-run`` or
``--apply``. Application startup never invokes this module.
"""
import argparse
import os

from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateColumn, CreateIndex, CreateTable

import app.models  # noqa: F401 - register metadata
from app.models.application import Application, ApplicationStatusHistory
from app.models.application_event import ApplicationEvent, HRCall
from app.models.bookmark import Bookmark
from app.models.document import Document
from app.models.interview import Interview, InterviewStatusHistory
from app.models.note import Note
from app.models.reminder import Reminder

TRACKER_MODELS = [
    Application, ApplicationStatusHistory, ApplicationEvent, HRCall, Bookmark,
    Interview, InterviewStatusHistory, Note, Document, Reminder,
]


def _tables():
    return [model.__table__ for model in TRACKER_MODELS]


def _count(connection, table):
    preparer = connection.dialect.identifier_preparer
    return connection.execute(text(f"SELECT count(*) FROM {preparer.quote(table)}")).scalar_one()


def _type_matches(column, actual, dialect):
    # Compare compiled SQL types, which captures String lengths and numeric types.
    expected_type = column.type.compile(dialect=dialect).upper()
    actual_type = actual.compile(dialect=dialect).upper()
    if expected_type == actual_type:
        return True
    # PostgreSQL reflects an unqualified SQLAlchemy Float as DOUBLE PRECISION
    # on existing columns, although the model compiles it as FLOAT. Treat only
    # these exact PostgreSQL spellings as aliases; retain strict checks for
    # precision-qualified floats and all other type differences.
    return dialect.name == "postgresql" and {
        expected_type,
        actual_type,
    } == {"FLOAT", "DOUBLE PRECISION"}


def _unique_column_sets(inspector, table: str) -> set[tuple[str, ...]]:
    """Collect actual unique constraints and unique indexes distinctly from ordinary indexes."""
    unique = {
        tuple(item["column_names"])
        for item in inspector.get_unique_constraints(table)
    }
    unique.update(
        tuple(item["column_names"])
        for item in inspector.get_indexes(table)
        if item.get("unique")
    )
    return unique


def _foreign_key_signature(columns, referred_table, referred_columns):
    return (tuple(columns), referred_table, tuple(referred_columns))


def _delete_action(action) -> str:
    # PostgreSQL reports omitted ON DELETE as NO ACTION; SQLAlchemy uses None.
    return (action or "NO ACTION").upper()


def _requires_remote_apply_ack(url: str, *, apply: bool, allow_remote: bool) -> bool:
    return apply and not url.startswith("sqlite") and not allow_remote


def _index_redundant_with_primary_key(index, primary_key_columns) -> bool:
    """A same-column index duplicates the primary key's unique index."""
    return bool(primary_key_columns) and tuple(c.name for c in index.columns) == tuple(primary_key_columns)


def database_target(url: str) -> tuple[str, str]:
    """Return only host and database name, excluding URL credentials."""
    parsed = make_url(url)
    return parsed.host or "(local)", parsed.database or "(default)"


def select_database_url(
    *, dry_run: bool, test_database_url: str | None
) -> str:
    """Select the explicit test URL for both modes; never use app config here."""
    if not test_database_url:
        mode = "--dry-run" if dry_run else "--apply"
        raise ValueError(f"{mode} requires CAREERTRACK_TEST_DATABASE_URL to be set.")
    return test_database_url


def validate_expected_test_host(url: str, expected_host: str | None) -> None:
    """Fail closed unless the selected URL names the explicitly expected host."""
    if not expected_host or not expected_host.strip():
        raise ValueError("CAREERTRACK_EXPECTED_TEST_HOST must be set before database access.")
    actual_host, _ = database_target(url)
    normalize = lambda host: host.strip().rstrip(".").casefold()
    if normalize(actual_host) != normalize(expected_host):
        raise ValueError("Selected database host does not match CAREERTRACK_EXPECTED_TEST_HOST.")


def plan(engine: Engine) -> list[str]:
    """Return planned changes, raising before any write for unsafe differences."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    actions = []
    with engine.connect() as connection:
        for model in TRACKER_MODELS:
            table = model.__tablename__
            if table not in existing:
                actions.append(f"CREATE TABLE: {table}")
                continue
            rows = _count(connection, table)
            cols = {c["name"]: c for c in inspector.get_columns(table)}
            # Check additions first. A populated table missing a required field
            # cannot be safely backfilled; report that before unrelated drift.
            for column in model.__table__.columns:
                if column.name not in cols:
                    if rows and not column.nullable and column.server_default is None:
                        raise RuntimeError(
                            f"Refusing to migrate non-empty legacy table {table}: "
                            f"non-empty and required column {column.name} has no database default"
                        )
                    actions.append(f"ADD COLUMN: {table}.{column.name}")
            primary_key_columns = tuple(inspector.get_pk_constraint(table).get("constrained_columns") or ())
            for column in model.__table__.columns:
                if column.name not in cols:
                    continue
                actual = cols[column.name]
                if not _type_matches(column, actual["type"], engine.dialect):
                    raise RuntimeError(f"Unsafe type mismatch: {table}.{column.name} is {actual['type']}; model requires {column.type}")
                # SQLite commonly reports INTEGER PRIMARY KEY as nullable even
                # though the primary-key constraint enforces non-null values.
                sqlite_primary_key = engine.dialect.name == "sqlite" and column.name in primary_key_columns
                if not sqlite_primary_key and bool(actual["nullable"]) != bool(column.nullable):
                    raise RuntimeError(f"Unsafe nullability mismatch: {table}.{column.name}")

            actual_fks = {
                _foreign_key_signature(f["constrained_columns"], f["referred_table"], f["referred_columns"]): {
                    "ondelete": _delete_action(f.get("options", {}).get("ondelete")),
                    "name": f.get("name"),
                }
                for f in inspector.get_foreign_keys(table)
            }
            for fk in model.__table__.foreign_key_constraints:
                sig = (tuple(c.parent.name for c in fk.elements), next(iter(fk.elements)).column.table.name, tuple(e.column.name for e in fk.elements))
                expected_delete = _delete_action(fk.ondelete)
                actual = actual_fks.get(sig)
                if actual is None:
                    actions.append(f"ADD FOREIGN KEY: {table}.{sig[0]} -> {sig[1]}.{sig[2]}")
                elif actual["ondelete"] != expected_delete:
                    actions.append(
                        f"REPLACE FOREIGN KEY: {table}.{actual['name']} "
                        f"(ON DELETE {actual['ondelete']} -> {expected_delete})"
                    )

            actual_indexes = {tuple(i["column_names"]) for i in inspector.get_indexes(table)}
            actual_unique = _unique_column_sets(inspector, table)
            for index in model.__table__.indexes:
                cols_key = tuple(c.name for c in index.columns)
                if _index_redundant_with_primary_key(index, primary_key_columns):
                    continue
                if cols_key not in actual_indexes:
                    actions.append(f"ADD INDEX: {index.name or table + '_' + '_'.join(cols_key)}")
            for constraint in model.__table__.constraints:
                if constraint.__class__.__name__ != "UniqueConstraint":
                    continue
                cols_key = tuple(c.name for c in constraint.columns)
                if cols_key not in actual_unique:
                    # Legacy placeholders may not yet contain the columns. Do
                    # not issue a query against a schema that cannot support it.
                    if not set(cols_key).issubset(cols):
                        continue
                    duplicate = connection.execute(text(
                        "SELECT 1 FROM " + engine.dialect.identifier_preparer.quote(table) +
                        " GROUP BY " + ", ".join(engine.dialect.identifier_preparer.quote(c) for c in cols_key) +
                        " HAVING count(*) > 1 LIMIT 1"
                    )).first()
                    if duplicate:
                        raise RuntimeError(f"Unsafe: duplicate values prevent unique constraint on {table}({', '.join(cols_key)})")
                    actions.append(f"ADD UNIQUE: {constraint.name or table + '_' + '_'.join(cols_key)}")
    return actions


def preview(engine: Engine) -> list[str]:
    return plan(engine)


def upgrade(engine: Engine) -> list[str]:
    """Apply only model-aligned repairs; all DDL is in one transaction."""
    actions = plan(engine)  # complete preflight before opening write transaction
    if engine.dialect.name not in ("postgresql", "sqlite"):
        raise RuntimeError("Migration supports PostgreSQL and SQLite only")
    if engine.dialect.name == "sqlite" and any(
        a.startswith(("ADD FOREIGN KEY", "REPLACE FOREIGN KEY")) for a in actions
    ):
        # SQLite cannot add a foreign key constraint in-place. Surface this
        # limitation in the returned plan; PostgreSQL apply remains complete.
        actions = [
            f"SQLITE LIMITATION (foreign key not altered): {action}"
            if action.startswith(("ADD FOREIGN KEY:", "REPLACE FOREIGN KEY:")) else action
            for action in actions
        ]

    with engine.begin() as connection:
        present = set(inspect(connection).get_table_names())
        missing = [t for t in _tables() if t.name not in present]
        if missing:
            from app.core.database import Base
            missing_names = {table.name for table in missing}
            for table in Base.metadata.sorted_tables:
                if table.name not in missing_names:
                    continue
                connection.execute(CreateTable(table))
                pk_columns = tuple(c.name for c in table.primary_key.columns)
                for index in table.indexes:
                    if not _index_redundant_with_primary_key(index, pk_columns):
                        connection.execute(CreateIndex(index))
        if engine.dialect.name == "sqlite":
            preparer = connection.dialect.identifier_preparer
            for model in TRACKER_MODELS:
                table = model.__table__
                if table.name not in present:
                    continue
                existing_columns = {c["name"] for c in inspect(connection).get_columns(table.name)}
                for column in table.columns:
                    if column.name not in existing_columns:
                        ddl = str(CreateColumn(column).compile(dialect=connection.dialect))
                        connection.exec_driver_sql(
                            f"ALTER TABLE {preparer.quote(table.name)} ADD COLUMN {ddl}"
                        )
                existing_indexes = {
                    tuple(index["column_names"])
                    for index in inspect(connection).get_indexes(table.name)
                }
                pk_columns = tuple(
                    inspect(connection).get_pk_constraint(table.name).get("constrained_columns") or ()
                )
                for index in table.indexes:
                    if _index_redundant_with_primary_key(index, pk_columns):
                        continue
                    if tuple(c.name for c in index.columns) not in existing_indexes:
                        connection.execute(CreateIndex(index))
                existing_unique = _unique_column_sets(inspect(connection), table.name)
                for constraint in table.constraints:
                    if constraint.__class__.__name__ != "UniqueConstraint":
                        continue
                    cols_key = tuple(c.name for c in constraint.columns)
                    if cols_key not in existing_unique:
                        name = constraint.name or f"uq_{table.name}_{'_'.join(cols_key)}"
                        columns_sql = ", ".join(preparer.quote(c) for c in cols_key)
                        connection.exec_driver_sql(
                            f"CREATE UNIQUE INDEX {preparer.quote(name)} "
                            f"ON {preparer.quote(table.name)} ({columns_sql})"
                        )
        if engine.dialect.name == "postgresql":
            preparer = connection.dialect.identifier_preparer
            for model in TRACKER_MODELS:
                table = model.__table__
                if table.name not in present:
                    continue
                current_cols = {c["name"] for c in inspect(connection).get_columns(table.name)}
                for column in table.columns:
                    if column.name not in current_cols:
                        ddl = str(CreateColumn(column).compile(dialect=connection.dialect))
                        connection.exec_driver_sql(f"ALTER TABLE {preparer.quote(table.name)} ADD COLUMN {ddl}")
                actual_fks = {
                    _foreign_key_signature(f["constrained_columns"], f["referred_table"], f["referred_columns"]): f
                    for f in inspect(connection).get_foreign_keys(table.name)
                }
                for n, fk in enumerate(table.foreign_key_constraints):
                    elems = list(fk.elements)
                    sig = (tuple(e.parent.name for e in elems), elems[0].column.table.name, tuple(e.column.name for e in elems))
                    old_fk = actual_fks.get(sig)
                    if old_fk is None or _delete_action(old_fk.get("options", {}).get("ondelete")) != _delete_action(fk.ondelete):
                        if old_fk is not None:
                            if not old_fk.get("name"):
                                raise RuntimeError(f"Cannot safely replace unnamed PostgreSQL foreign key on {table.name}")
                            connection.exec_driver_sql(
                                f"ALTER TABLE {preparer.quote(table.name)} DROP CONSTRAINT "
                                f"{preparer.quote(old_fk['name'])}"
                            )
                        name = fk.name or f"fk_{table.name}_{'_'.join(sig[0])}_{n}"
                        connection.exec_driver_sql(
                            f"ALTER TABLE {preparer.quote(table.name)} ADD CONSTRAINT {preparer.quote(name)} "
                            f"FOREIGN KEY ({', '.join(preparer.quote(c) for c in sig[0])}) REFERENCES {preparer.quote(sig[1])} "
                            f"({', '.join(preparer.quote(c) for c in sig[2])}) ON DELETE {fk.ondelete or 'NO ACTION'}"
                        )
                for index in table.indexes:
                    pk_columns = tuple(
                        inspect(connection).get_pk_constraint(table.name).get("constrained_columns") or ()
                    )
                    if _index_redundant_with_primary_key(index, pk_columns):
                        continue
                    names = {tuple(i["column_names"]) for i in inspect(connection).get_indexes(table.name)}
                    if tuple(c.name for c in index.columns) not in names:
                        connection.execute(CreateIndex(index))
                for constraint in table.constraints:
                    if constraint.__class__.__name__ == "UniqueConstraint":
                        names = _unique_column_sets(inspect(connection), table.name)
                        if tuple(c.name for c in constraint.columns) not in names:
                            cols = ", ".join(preparer.quote(c.name) for c in constraint.columns)
                            name = constraint.name or f"uq_{table.name}_{'_'.join(c.name for c in constraint.columns)}"
                            connection.exec_driver_sql(f"ALTER TABLE {preparer.quote(table.name)} ADD CONSTRAINT {preparer.quote(name)} UNIQUE ({cols})")
    # Preserve the established upgrade() return format for added columns.
    return [
        action.removeprefix("ADD COLUMN: ")
        if action.startswith("ADD COLUMN: ") else action
        for action in actions
    ]


def main():
    parser = argparse.ArgumentParser(description="Inspect or repair the M2 tracker schema")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="read-only schema and data preflight")
    group.add_argument("--apply", action="store_true", help="apply the reviewed M2 schema repair")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="acknowledge applying changes to a non-SQLite database",
    )
    args = parser.parse_args()
    from sqlalchemy import create_engine
    try:
        url = select_database_url(
            dry_run=args.dry_run,
            test_database_url=os.environ.get("CAREERTRACK_TEST_DATABASE_URL"),
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.apply:
        is_sqlite = url.startswith("sqlite")
        is_postgres = url.startswith(("postgres://", "postgresql://", "postgresql+"))
        if not (is_sqlite or is_postgres):
            parser.error("--apply supports only SQLite test databases or PostgreSQL test databases.")
        if _requires_remote_apply_ack(
            url, apply=True, allow_remote=args.allow_remote
        ):
            parser.error("Applying to a remote database requires --allow-remote.")
    try:
        validate_expected_test_host(
            url, os.environ.get("CAREERTRACK_EXPECTED_TEST_HOST")
        )
    except ValueError as exc:
        parser.error(str(exc))
    host, database = database_target(url)
    print(f"Database target: host={host} database={database}")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        if args.dry_run:
            print("DRY RUN: read-only; no changes will be made.")
            actions = preview(engine)
        else:
            actions = upgrade(engine)
        for action in actions:
            print(f"- {action}")
        if not actions:
            print("No M2 schema changes required.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
