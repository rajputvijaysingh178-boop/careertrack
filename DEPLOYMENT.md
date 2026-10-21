# Deployment and environment configuration

## Database and secret handling

The application reads settings from process environment variables first, then `.env`, then code
defaults. Do not commit `.env` or place any database URL, JWT signing secret, admin password, or AI
key in frontend assets. `.env.example` contains placeholders only. Set a local SQLite URL for local
development and a separate test-only URL for test utilities; never reuse a production URL for either.
The application normalizes standard `postgresql://` URLs to SQLAlchemy's `postgresql+psycopg://`
dialect; explicit driver URLs are preserved.

| Variable | Requirement | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Required for deployment | Neon connection string, stored only in backend host secrets. Use the pooled connection string with TLS (`sslmode=require`) where appropriate. |
| `SECRET_KEY` | Required for PostgreSQL deployment | Random JWT signing secret, at least 32 characters. The legacy `JWT_SECRET` name remains accepted for compatibility; prefer `SECRET_KEY` for new configuration. |
| `CORS_ORIGINS` | Required when frontend is on another origin | Exact comma-separated HTTPS origins for the frontend. Same-origin `/tracker/` deployment does not need cross-origin access. Wildcard origins are not the default. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Optional after initial setup | Read by explicit admin provisioning tools. Normal application startup does not create an admin; use the guarded provisioning command after confirming the target host. Keep the password in backend secrets. |
| `APP_NAME`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Application label and JWT settings. The default algorithm is HS256 and token lifetime is 1440 minutes. |
| `ENABLE_SCHEDULER` | Optional | Enables hourly job expiry and minute-level reminders. Use one API worker with this enabled, or disable it and schedule equivalent external jobs when scaling to multiple workers. |
| `SEED_DEFAULT_SKILLS` | Reserved | The normal app startup does not currently invoke the default-skill seeder, so this setting has no effect. |
| `AUTO_CREATE_SCHEMA` | Optional | Defaults to enabled only for SQLite and disabled for PostgreSQL. Keep it disabled for Neon; apply a reviewed migration separately. |
| `LLM_API_KEY`, `LLM_MODEL` | Optional | Gemini API key and model ID for AI enrichment. Set LLM_API_KEY from Google AI Studio; LLM_MODEL defaults to gemini-3.8-flash. JD analysis and interview prep plans fall back to rule-based output when Gemini is disabled or unavailable. Keep the key only in backend .env or a secret store. |
| `MATERIAL_UPLOAD_DIR`, `MAX_MATERIAL_UPLOAD_BYTES` | Optional | Writable persistent directory and size limit for admin-uploaded study materials. The default maximum is 10 MiB. |

## Hosting layout

The repository has no provider-specific deployment manifest. The UI can still be served by FastAPI
at `/tracker/` for same-origin use. For Render, configure the backend service to run:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Add the production `DATABASE_URL`, `SECRET_KEY`, and (for split origins) `CORS_ORIGINS` as secret or
environment settings in Render. Never expose backend secrets as frontend configuration.

### Separate Vercel frontend

The frontend is static HTML/CSS/JavaScript and needs no build step. Set the Vercel project Root
Directory to `frontend/tracker`, Framework Preset to `Other`, leave the Build Command blank, and use
`.` as the Output Directory. The frontend's CSS, script, and brand links are relative to this root.
Set the public Render API origin in `frontend/tracker/api-config.js`:

```js
window.CAREERTRACK_API_BASE_URL = 'https://<render-service>.onrender.com';
```

For same-origin local development or FastAPI's `/tracker/` UI, leave the value as an empty string.
This browser-visible setting is only an API origin; never put credentials or secrets in it. All API
requests, including multipart resume matching, material upload, and material download, use the shared
URL helper and retain bearer-token authentication.

In Render's backend environment, set `CORS_ORIGINS` to the exact Vercel origin(s), comma-separated,
with no paths or trailing slash. For example:

```text
CORS_ORIGINS=https://<vercel-project>.vercel.app,https://<frontend-custom-domain>
```

Add each intentionally used preview origin explicitly. The API uses bearer tokens in the
`Authorization` header and does not require credentialed cookies. Do not use `*` for production.

Material uploads are written to local disk. Hosts with ephemeral filesystems must mount a persistent
volume and set `MATERIAL_UPLOAD_DIR` to its writable path, or switch uploads to object storage before
relying on uploaded files across deploys.

## Phase 5D operational review

### Runtime and environment names

`requirements.txt` is the dependency manifest; there is no `pyproject.toml` or provider
manifest. Use Python 3.10 or newer (Python 3.11 is the deployment baseline); the source uses
modern type syntax. Render's start command is `uvicorn app.main:app --host 0.0.0.0 --port
$PORT`. Do not add multiple Uvicorn workers while the in-process scheduler is enabled.

Production requires `DATABASE_URL` and `SECRET_KEY`; PostgreSQL requires a random signing key
of at least 32 characters. `JWT_SECRET` is accepted as a legacy alias. For split origins,
configure `CORS_ORIGINS`. Optional settings are `APP_NAME`, `ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `ENABLE_SCHEDULER`, `AUTO_CREATE_SCHEMA`,
`MATERIAL_UPLOAD_DIR`, `MAX_MATERIAL_UPLOAD_BYTES`, `LLM_API_KEY`, and `LLM_MODEL`.
`ADMIN_NAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` are used only by explicit provisioning
tools; normal startup does not bootstrap accounts. `SEED_DEFAULT_SKILLS` is reserved and has
no startup effect. Alembic tools separately require process variables
`CAREERTRACK_ALEMBIC_DATABASE_URL` and, for PostgreSQL,
`CAREERTRACK_ALEMBIC_EXPECTED_HOST`. Use placeholders in documentation only and store actual
values in backend secrets or a short-lived process environment.

### Material storage and access

`POST /materials/upload` is ADMIN-only. It reads at most
`MAX_MATERIAL_UPLOAD_BYTES + 1` bytes (default 10 MiB), rejects empty or oversize uploads,
allows only PDF, DOC/DOCX, PPT/PPTX, TXT, and MD extensions, and stores the validated
extension under a random UUID filename. The client filename is not used as a path. Set
`MATERIAL_UPLOAD_DIR` to a writable Render disk mount path (for example,
`/var/data/careertrack/materials` after mounting a disk there); the existing implementation
works with that path without a storage-provider change. Existing ephemeral uploads are not
migrated automatically.

Authenticated users can list and download; only admins can upload, update, and delete. Missing
local files return not-found. Local reads resolve paths and enforce containment under the
upload directory; deletion only unlinks files directly in that directory. External material
URLs redirect authenticated users, so admins should use trusted destinations. Upload size is
bounded in application memory, but configure a request-body limit at the proxy/host as well.
Extension checking does not validate file content or scan malware. Database/file operations
are not transactional: failed metadata writes can leave orphan files, while failed metadata
deletes after file removal can leave a broken record. There is no orphan cleanup. A persistent
disk is suitable for one service instance; use object storage when multiple instances need
shared files or independent file lifecycle/backup is required.

### Vercel, CORS, scheduler and authentication

The Vercel static project uses Root Directory `frontend/tracker`, Framework Preset `Other`,
blank Build Command, and Output Directory `.`. Its only API-origin setting is the public
`window.CAREERTRACK_API_BASE_URL` in `api-config.js`, set to the Render origin; no secret or
API key belongs in frontend configuration. The HTML uses relative static asset paths, and all
requests use `api-client.js`, including JSON calls, resume-match multipart, and material
downloads. For split origins, Render `CORS_ORIGINS` is comma-separated exact origins with
scheme and hostname only, no path or trailing slash, e.g.
`https://<project>.vercel.app,https://<custom-domain>`. Add only intentionally supported
preview origins.

`ENABLE_SCHEDULER=true` starts APScheduler inside each API process: hourly job expiry and
minute-level reminder status updates (not email delivery). Use one process with it enabled.
Before scaling to multiple instances/workers, disable it in API processes and run a single
external scheduler/worker; add idempotency or a distributed lock if duplicate runs could
matter.

JWT expiry is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440). The browser stores
tokens in local storage; logout clears only that local copy. There is no server-side revocation,
so copied tokens remain valid until expiry; password changes also do not revoke issued tokens.
Use HTTPS, a unique random signing secret, and choose a shorter lifetime if appropriate.
Public `/auth/register` has no role field and creates a USER, so it cannot assign ADMIN. No
account was provisioned or modified in this phase.

### Migration comparison and readiness

For a later schema comparison, start with an isolated local database, then use a separately
approved test branch after confirming its target hostname out of band. Set the explicit
Alembic URL and expected host in the process environment and run `python -m alembic check`;
this connects and compares metadata but does not apply schema changes. Inspect columns, types,
nullability, defaults, keys, constraints and meaningful indexes. An empty database is handled
by the initial `upgrade head`, which creates tables. An existing database must match the full
initial snapshot before an explicitly approved `stamp 20261012_0001` records its baseline
without creating application tables. A partial or drifted schema needs a reviewed,
data-preserving reconciliation revision. Neither comparison against a live database nor any
migration was performed in Phase 5D.

Verified from source: PostgreSQL startup skips `create_all` even when
`AUTO_CREATE_SCHEMA=true`; Alembic requires an explicit target and expected-host check; the
frontend API requests share one URL/auth helper; file uploads use bounded reads and UUID
names; and the scheduler runs per process. Runtime validation is still required for Render
startup/health/database connectivity, Vercel-to-Render preflight CORS, authentication, disk
mount permissions and persistence across deploys, and authorized upload/download/missing-file
behavior.

Remaining decisions before deployment: confirm the database branch and migration baseline;
select the initial admin provisioning process; finalize production/custom/preview domains;
choose upload retention, backup and host request-size limits; and decide scheduler ownership
before scaling. No deployment or live-database action was performed. Stop here for Phase 5D.

## Schema safety

Alembic is configured under `alembic/` with an initial versioned snapshot for the 22 registered
SQLAlchemy model tables. Revision `20261012_0001` creates a new, empty database; it is not an upgrade
for an existing application database. PostgreSQL startup never performs schema DDL, even if
`AUTO_CREATE_SCHEMA=true`; SQLite retains its local-development convenience. The separate
`scripts/migrate_m2_schema.py` remains a guarded, additive M2 repair helper and is not the general
schema migration path. The legacy `scripts/seed_demo.py` helper is restricted to SQLite and must not
be used to create PostgreSQL schema. No migration or seeder was run as part of this phase.

### Migration target and existing-schema baseline

Alembic requires `CAREERTRACK_ALEMBIC_DATABASE_URL`; it never reads `DATABASE_URL` or `.env` as a
fallback. For PostgreSQL, it also requires `CAREERTRACK_ALEMBIC_EXPECTED_HOST` and checks it against
the URL hostname before connecting. Use a short-lived shell session and do not print either value.

For isolated local validation, run `python -m pytest -q tests/test_migrations` (the test creates and
upgrades a temporary SQLite database). For a later, explicitly approved validation on an empty
Neon test branch, first load `CAREERTRACK_TEST_DATABASE_URL` securely into the current PowerShell
session, then use:

```powershell
$env:CAREERTRACK_ALEMBIC_DATABASE_URL = $env:CAREERTRACK_TEST_DATABASE_URL
$env:CAREERTRACK_ALEMBIC_EXPECTED_HOST = '<confirmed-test-branch-hostname>'
python -m alembic upgrade head
```

That command writes schema and is not part of this review. For an existing branch, first verify the
entire schema against the initial revision. If the database is empty, `upgrade head` is appropriate.
If every table, column, type, nullability rule, default, key, meaningful index, and constraint already
matches (ignoring only standalone indexes that duplicate a primary-key index), record the baseline
without creating application tables using:

```powershell
python -m alembic stamp 20261012_0001
```

Stamping still writes Alembic's version record and must be explicitly approved. Never stamp based
only on matching table names. If any part of the schema differs or only some tables exist, do not
run either command; author and review a data-preserving reconciliation revision first. No current
Neon schema was inspected during this phase.

Before a future production migration, take and verify a Neon backup/restore point, validate the exact
revision sequence on an isolated database and then the test branch, inspect generated SQL, and
schedule a maintenance window. PostgreSQL DDL in each Alembic revision runs in a transaction here.
The initial revision has no destructive downgrade. Rollback means restoring the verified backup or
applying a separately reviewed forward repair; do not drop tables or columns as an automatic
rollback strategy.

| Test-only utility | Required target configuration | Notes |
| --- | --- | --- |
| `scripts/migrate_m2_schema.py` | Process variables `CAREERTRACK_TEST_DATABASE_URL` and `CAREERTRACK_EXPECTED_TEST_HOST` | Uses only the explicit test URL, verifies its host before connecting; remote `--apply` also requires `--allow-remote`. |
| `scripts/seed_recommendation_demo.py` | Process variables `CAREERTRACK_TEST_DATABASE_URL` and `CAREERTRACK_EXPECTED_TEST_HOST` | Requires the confirmed test host and explicit `--apply`; it does not use the application's database setting. |
| `scripts/provision_admin.py` | `DATABASE_URL`, `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and process variable `CAREERTRACK_EXPECTED_TEST_HOST` | Uses the normal settings loader, then checks the configured PostgreSQL host against the expected host before opening a session. Set `DATABASE_URL` to the test branch for this utility; the expected-host check is an acknowledgement guard, not automatic environment separation. |

Keep target URLs and expected-host acknowledgements in a short-lived test-only shell session. Do not put `CAREERTRACK_TEST_DATABASE_URL` or `CAREERTRACK_EXPECTED_TEST_HOST` in `.env`; the migration/demo scripts intentionally read them from the process environment. The provisioner uses `DATABASE_URL` instead, so verify its selected target is the test database before invoking it.

## Local and deployment checks

For local development, copy `.env.example` to `.env`; its `DATABASE_URL` points only to a local
SQLite file, which is ignored by Git. Replace the local `SECRET_KEY` placeholder with a private
random value. Deployment must set its own backend `DATABASE_URL` and `SECRET_KEY` out of band.
The browser UI uses same-origin API paths when `CAREERTRACK_API_BASE_URL` is empty; for Vercel,
configure the public Render origin in `frontend/tracker/api-config.js` as described above.

The root test fixture forces `DATABASE_URL=sqlite://`, a test-only `SECRET_KEY`, local test CORS
origins, and `ENABLE_SCHEDULER=false` before importing the app. Database tests use isolated SQLite
engines/metadata; they do not connect to Neon. For local testing, run `venv\\Scripts\\python.exe -m pytest -q` on
Windows or `python -m pytest -q` on Unix-like systems. After setting deployment variables in the
backend host, verify startup and database connectivity using that host's health/log view. Do not
paste the Neon URL or secret values into logs, issue reports, or frontend code.
