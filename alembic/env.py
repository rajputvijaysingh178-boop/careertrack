"""Alembic environment with explicit database-target acknowledgement.

Migrations never fall back to the application's DATABASE_URL or .env. Remote
PostgreSQL targets require a separate expected-host acknowledgement before any
connection is opened.
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

import app.models  # noqa: F401 - register every table in metadata
from app.core.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def selected_database_url() -> str:
    url = os.environ.get("CAREERTRACK_ALEMBIC_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "Set CAREERTRACK_ALEMBIC_DATABASE_URL explicitly; Alembic will not fall back to DATABASE_URL."
        )
    parsed = make_url(url)
    if parsed.get_backend_name() == "postgresql":
        expected_host = os.environ.get("CAREERTRACK_ALEMBIC_EXPECTED_HOST", "").strip()
        actual_host = parsed.host or ""
        normalize = lambda value: value.strip().rstrip(".").casefold()
        if not expected_host:
            raise RuntimeError(
                "Set CAREERTRACK_ALEMBIC_EXPECTED_HOST before using a PostgreSQL migration target."
            )
        if normalize(actual_host) != normalize(expected_host):
            raise RuntimeError(
                "CAREERTRACK_ALEMBIC_DATABASE_URL host does not match CAREERTRACK_ALEMBIC_EXPECTED_HOST."
            )
    elif parsed.get_backend_name() != "sqlite":
        raise RuntimeError("Alembic supports only explicitly configured SQLite or PostgreSQL targets.")
    return url


def include_object(obj, name, type_, reflected, compare_to):
    """Ignore model indexes that duplicate an equivalent primary-key index."""
    if type_ != "index":
        return True
    table = obj.table
    index_columns = tuple(column.name for column in obj.columns)
    primary_key_columns = tuple(column.name for column in table.primary_key.columns)
    return not primary_key_columns or index_columns != primary_key_columns


def run_migrations_offline() -> None:
    url = selected_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = selected_database_url()
    connectable = create_engine(url, pool_pre_ping=True)
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                include_object=include_object,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
