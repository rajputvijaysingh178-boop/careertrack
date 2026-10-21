# CareerTrack

Job Application & Interview Preparation Platform (FastAPI).
Architecture: **Router -> Service -> Repository -> Database**

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs (every module has a `/ping` endpoint).

Gemini is optional. This checkout loads `.env` from the parent directory (`../.env`). See
`.env.example` for placeholders; preserve any existing `.env` and add
`LLM_API_KEY=<your-private-Google-AI-Studio-key>` there and optionally set
`LLM_MODEL=gemini-3.8-flash` (the current default). The project-root `.env.example` lists
the local variables without credentials. Keep your real key private. Set `use_ai: true`
on `POST /jd-analyzer/analyze` or `POST /prep/plan` to request AI enrichment; otherwise
both features use their rule-based behavior. Run the backend with `uvicorn app.main:app --reload`.

Run tests: `pytest`

## Frontend
The job board, application tracker, M3 preparation tools, and admin workspace are
served at `/tracker/`.

## Environment and deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for required and optional settings, Neon PostgreSQL
configuration, CORS, file storage, AI configuration, and same-origin/split-host deployment notes.

## Application tracker database upgrade
Before using the M2 tracker APIs with an
older database created from the original placeholder models, run
`python -m scripts.migrate_m2_schema --apply` against a local SQLite copy first.
The migration is additive and refuses non-empty placeholder tracker tables; it
does not delete tables or records. Remote databases require the explicit
`--allow-remote` flag after a backup and target review.
Automatic schema creation is enabled by default only for SQLite. PostgreSQL deployments require an
explicit reviewed schema upgrade before tracker APIs are used; app startup will not alter PostgreSQL.

## Ownership
| Member | Scope |
|---|---|
| M1 | Auth, admin, companies, jobs, skills, search, blogs, materials, job expiry |
| M2 | Bookmarks, Apply & Track, state machine, timeline, interviews, notes, reminders, kanban, analytics |
| M3 | Interview questions, recommendations, JD analyzer, resume match, prep plan, skill gap |

Every file starts with an `OWNER:` line in its docstring.

## Git workflow
Branches `feature/m1-*`, `feature/m2-*`, `feature/m3-*` -> PR into `develop`.
M1 pushes core models (users, companies, jobs, skills) first.

## Neon test data (admin and user panels)

The normal `scripts.seed_demo` helper is local-SQLite-only. For the explicitly confirmed
CareerTrack TEST Neon branch, use the guarded seeder below. It does **not** create tables,
run migrations, or use production. It checks the target hostname and required existing tables
before writing anything.

In PowerShell, from the project root:

```powershell
$env:CAREERTRACK_EXPECTED_TEST_HOST = "ep-wandering-mountain-b3xa8gdn.c-4.ap-southeast-1.aws.neon.tech"
python -m scripts.seed_test_data
```

The first command runs a read-only plan. If it reports missing required tables or columns,
stop and reconcile the schema first. If the plan is correct, explicitly insert missing demo
records with:

```powershell
python -m scripts.seed_test_data --apply
```

The script is idempotent for its labelled demo records and never changes an existing account's
role. Demo credentials (TEST ONLY):

- Admin panel: `admin.demo@careertrack.test` / `DemoAdmin!2026`
- User panel: `user.demo@careertrack.test` / `DemoUser!2026`

Demo jobs, notes, interview records, reminders, questions, and materials are labelled as test data.
Do not use these demo credentials outside the test environment.
