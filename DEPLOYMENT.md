# Deployment and environment configuration

## Database and secret handling

The application reads settings from environment variables, with `.env` used for local development.
Do not commit `.env` or place any database URL, JWT signing secret, admin password, or AI key in
frontend assets. `.env.example` contains placeholders only. The current configured local database
URL was inspected without displaying its credentials: it uses Neon PostgreSQL with the `psycopg`
driver. `requirements.txt` installs that driver. Standard `postgresql://` Neon URLs are normalized
to SQLAlchemy's `postgresql+psycopg://` dialect; explicit driver URLs are preserved.

| Variable | Requirement | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Required for deployment | Neon connection string, stored only in backend host secrets. Use the pooled connection string with TLS (`sslmode=require`) where appropriate. |
| `SECRET_KEY` | Required for PostgreSQL deployment | Random JWT signing secret, at least 32 characters. The legacy `JWT_SECRET` name remains accepted so existing local config continues to work. |
| `CORS_ORIGINS` | Required when frontend is on another origin | Exact comma-separated HTTPS origins for the frontend. Same-origin `/tracker/` deployment does not need cross-origin access. Wildcard origins are not the default. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Optional after initial setup | Used only to create the first admin when one does not already exist. Keep the password in backend secrets. |
| `APP_NAME`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Application label and JWT settings. The default algorithm is HS256 and token lifetime is 1440 minutes. |
| `ENABLE_SCHEDULER` | Optional | Enables hourly job expiry and minute-level reminders. Use one API worker with this enabled, or disable it and schedule equivalent external jobs when scaling to multiple workers. |
| `SEED_DEFAULT_SKILLS` | Optional | Seeds built-in skills when the database is first initialized. |
| `AUTO_CREATE_SCHEMA` | Optional | Defaults to enabled only for SQLite and disabled for PostgreSQL. Keep it disabled for Neon; apply a reviewed migration separately. |
| `LLM_API_KEY`, `LLM_MODEL` | Optional | Anthropic API key and model for AI enrichment. The rule-based preparation features work without them. |
| `MATERIAL_UPLOAD_DIR`, `MAX_MATERIAL_UPLOAD_BYTES` | Optional | Writable persistent directory and size limit for admin-uploaded study materials. The default maximum is 10 MiB. |

## Hosting layout

The repository has no Render, Railway, Fly.io, Vercel, Netlify, or other provider-specific
deployment manifest, so a particular host cannot be confirmed from the project. The current UI is
served by FastAPI at `/tracker/`; that is the simplest same-origin deployment and needs no separate
frontend build or frontend secret. Configure the backend service to run:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Add the production `DATABASE_URL`, `SECRET_KEY`, and (for split origins) `CORS_ORIGINS` as secret or
environment settings in the backend host's dashboard. If the frontend is deployed separately, it
must be served from the origin listed in `CORS_ORIGINS`; the current UI uses relative API paths and
therefore expects a same-origin reverse proxy or the same FastAPI host. Do not expose backend
secrets as frontend build variables.

Material uploads are written to local disk. Hosts with ephemeral filesystems must mount a persistent
volume and set `MATERIAL_UPLOAD_DIR` to its writable path, or switch uploads to object storage before
relying on uploaded files across deploys.

## Schema safety

There is currently no Alembic configuration or versioned revision in `alembic/`; the directory only
contains a README. The app uses `Base.metadata.create_all()` only for SQLite by default; it creates
missing tables but does not alter existing tables. PostgreSQL startup does not perform schema DDL.
The separate `scripts/migrate_m2_schema.py` is an
additive M2 migration helper that refuses non-empty legacy placeholder tables. Do not point either
schema mechanism at Neon until the existing schema has been reviewed and backed up. No migration was
run as part of this configuration audit. A proper Alembic baseline/upgrade plan must be prepared
against a schema snapshot before automated production migrations are enabled.

## Local and deployment checks

Tests override `DATABASE_URL` to in-memory SQLite before importing the app and disable its scheduler;
they do not connect to Neon. For local testing, run `venv\\Scripts\\python.exe -m pytest -q` on
Windows or `python -m pytest -q` on Unix-like systems. After setting deployment variables in the
backend host, verify startup and database connectivity using that host's health/log view. Do not
paste the Neon URL or secret values into logs, issue reports, or frontend code.
